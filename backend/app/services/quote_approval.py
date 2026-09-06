from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AuditEventType, QuotationStatus, RoleName
from app.engines.approval import ApprovalEngine
from app.models.quote_approval_step import QuoteApprovalStep
from app.models.quote_approval_trigger import QuoteApprovalTrigger
from app.models.quote_audit_event import QuoteAuditEvent
from app.models.quotation import Quotation
from app.models.user import User
from app.repositories.approval_policy import ApprovalPolicyRepository
from app.repositories.quote_approval_step import QuoteApprovalStepRepository
from app.repositories.quote_audit_event import QuoteAuditEventRepository
from app.repositories.quotation import QuotationRepository
from app.schemas.quote_approval import QuoteApprovalStepRead, QuoteSubmissionResponse
from app.services.exceptions import (
    QuoteAccessDeniedError,
    QuoteNotEditableError,
    QuoteNotFoundError,
    QuotationValidationError,
    ResourceNotFoundError,
)
from app.services.quotation_evaluation import QuotationEvaluationService


class QuoteApprovalService:
    """Service orchestrating automatic approval routing, chains, and approval decision processing."""

    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db
        self.quote_repo = QuotationRepository()
        self.step_repo = QuoteApprovalStepRepository()
        self.policy_repo = ApprovalPolicyRepository()
        self.audit_repo = QuoteAuditEventRepository()
        self.eval_service = QuotationEvaluationService(db)

    async def submit_quotation(self, quotation_id: int, current_user: User) -> QuoteSubmissionResponse:
        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")

        # 1. Verify editability
        if quote.status not in {QuotationStatus.DRAFT.value, QuotationStatus.RETURNED_FOR_REVISION.value}:
            raise QuoteNotEditableError(f"Quotation {quote.quote_number} is in '{quote.status}' status and cannot be submitted.")

        # Ownership check for Sales Rep
        is_admin = hasattr(current_user, "role") and current_user.role and current_user.role.name == RoleName.ADMIN
        if not is_admin and quote.sales_rep_id != current_user.id:
            raise QuoteAccessDeniedError("You do not have permission to submit this quotation.")

        if not quote.lines:
            raise QuotationValidationError("Cannot submit an empty quotation with zero product lines.")

        # 2. Recalculate quote
        await self.eval_service.evaluate_and_update(quote)

        # 3. Fetch active approval policies
        active_policies_orm = await self.policy_repo.list_policies(self.db, is_active=True, effective_only=True)
        active_policies = [
            {
                "id": p.id,
                "customer_tier_id": p.customer_tier_id,
                "discount_above_pct": p.discount_above_pct,
                "margin_below_pct": p.margin_below_pct,
                "payment_terms_above_days": p.payment_terms_above_days,
                "blended_risk_above": p.blended_risk_above,
                "approval_role": p.approval_role,
                "priority": p.priority,
            }
            for p in active_policies_orm
        ]

        has_line_over_max = any(
            (l.max_discount_pct_snapshot is not None and l.effective_discount_pct > l.max_discount_pct_snapshot)
            for l in quote.lines
        )

        customer_tier_id = quote.customer.tier_id if quote.customer else None

        # 4. Run Approval Engine
        eval_res = ApprovalEngine.evaluate(
            weighted_effective_discount_pct=quote.weighted_effective_discount_pct,
            margin_pct=quote.margin_pct,
            payment_terms_days=quote.payment_terms_days,
            blended_risk_score=quote.blended_risk_score,
            customer_tier_id=customer_tier_id,
            has_line_over_max_discount=has_line_over_max,
            active_policies=active_policies,
        )

        current_round = await self.step_repo.get_latest_round(self.db, quote.id) + 1
        now = datetime.now(timezone.utc)
        created_steps = []

        if eval_res.requires_approval:
            # Create Approval Steps for chain
            for seq, role_name in enumerate(eval_res.required_roles, start=1):
                step = QuoteApprovalStep(
                    quotation_id=quote.id,
                    approval_round=current_round,
                    sequence=seq,
                    approval_role=role_name,
                    status="PENDING",
                    requested_at=now,
                )
                await self.step_repo.create_step(self.db, step)

                # Attach triggers to first step
                if seq == 1:
                    for trg in eval_res.triggers:
                        trg_obj = QuoteApprovalTrigger(
                            approval_step_id=step.id,
                            approval_policy_id=trg.approval_policy_id,
                            trigger_code=trg.trigger_code,
                            actual_value=trg.actual_value,
                            threshold_value=trg.threshold_value,
                            message=trg.message,
                        )
                        self.db.add(trg_obj)

                created_steps.append(step)

            quote.status = eval_res.projected_status.value
            quote.submitted_at = now
            msg = f"Quotation submitted and routed for {eval_res.required_roles[0]} approval."

            # Audit event
            event = QuoteAuditEvent(
                quotation_id=quote.id,
                actor_user_id=current_user.id,
                event_type="QUOTE_SUBMITTED",
                from_status=QuotationStatus.DRAFT.value,
                to_status=quote.status,
                event_metadata={"approval_round": current_round, "required_roles": eval_res.required_roles},
            )
            self.db.add(event)
        else:
            quote.status = QuotationStatus.APPROVED.value
            quote.submitted_at = now
            msg = "Quotation auto-approved instantly with no policy threshold triggers."

            # Audit event
            event = QuoteAuditEvent(
                quotation_id=quote.id,
                actor_user_id=current_user.id,
                event_type="QUOTE_AUTO_APPROVED",
                from_status=QuotationStatus.DRAFT.value,
                to_status=QuotationStatus.APPROVED.value,
            )
            self.db.add(event)

        try:
            await self.db.commit()
            all_steps = await self.step_repo.list_by_quotation(self.db, quote.id)
            current_round_steps = [s for s in all_steps if s.approval_round == current_round]

            return QuoteSubmissionResponse(
                quotation_id=quote.id,
                status=quote.status,
                requires_approval=eval_res.requires_approval,
                approval_round=current_round,
                required_roles=eval_res.required_roles,
                steps=[QuoteApprovalStepRead.model_validate(s) for s in current_round_steps],
                message=msg,
            )
        except Exception:
            await self.db.rollback()
            raise

    async def list_approval_steps(self, quotation_id: int) -> List[QuoteApprovalStep]:
        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")
        return await self.step_repo.list_by_quotation(self.db, quotation_id)

    async def process_decision(
        self,
        quotation_id: int,
        step_id: int,
        action: str,  # 'APPROVE', 'REJECT', 'RETURN'
        reason: Optional[str],
        current_user: User,
    ) -> Quotation:
        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")

        step = await self.step_repo.get_by_id(self.db, step_id)
        if not step or step.quotation_id != quote.id:
            raise ResourceNotFoundError(f"Approval step {step_id} not found on quotation {quotation_id}.")

        if step.status != "PENDING":
            raise QuoteNotEditableError(f"Approval step {step_id} is already in '{step.status}' status.")

        # RBAC Check: User role must match step approval_role
        user_role_name = current_user.role.name if (hasattr(current_user, "role") and current_user.role) else ""
        if user_role_name != step.approval_role:
            raise QuoteAccessDeniedError(
                f"User role '{user_role_name}' is not authorized to decide step requiring '{step.approval_role}'."
            )

        # For sequence 2 (Finance), sequence 1 (Manager) must already be APPROVED
        if step.sequence > 1:
            all_steps = await self.step_repo.list_by_quotation(self.db, quote.id)
            prev_steps = [
                s for s in all_steps
                if s.approval_round == step.approval_round and s.sequence < step.sequence
            ]
            for ps in prev_steps:
                if ps.status != "APPROVED":
                    raise QuoteNotEditableError("Previous approval step in round must be approved first.")

        # Mandatory reason check for Reject or Return
        if action in {"REJECT", "RETURN"} and not (reason and reason.strip()):
            raise QuotationValidationError(f"Reason is mandatory when taking action '{action}'.")

        now = datetime.now(timezone.utc)

        if action == "APPROVE":
            step.status = "APPROVED"
            step.decided_by_user_id = current_user.id
            step.decision_reason = reason
            step.decided_at = now

            # Check if higher sequence step exists in same round
            all_steps = await self.step_repo.list_by_quotation(self.db, quote.id)
            next_steps = [
                s for s in all_steps
                if s.approval_round == step.approval_round and s.sequence > step.sequence and s.status == "PENDING"
            ]

            old_status = quote.status
            if next_steps:
                quote.status = QuotationStatus.PENDING_FINANCE_APPROVAL.value
            else:
                if getattr(step, "approval_context", "INITIAL") == "NEGOTIATION":
                    quote.status = QuotationStatus.SENT_TO_CUSTOMER.value
                else:
                    quote.status = QuotationStatus.APPROVED.value

            audit_evt = QuoteAuditEvent(
                quotation_id=quote.id,
                actor_user_id=current_user.id,
                event_type="APPROVAL_APPROVED",
                from_status=old_status,
                to_status=quote.status,
                reason=reason,
                event_metadata={"step_id": step.id, "role": step.approval_role},
            )
            self.db.add(audit_evt)

        elif action == "REJECT":
            step.status = "REJECTED"
            step.decided_by_user_id = current_user.id
            step.decision_reason = reason
            step.decided_at = now

            old_status = quote.status
            quote.status = QuotationStatus.REJECTED.value

            audit_evt = QuoteAuditEvent(
                quotation_id=quote.id,
                actor_user_id=current_user.id,
                event_type="APPROVAL_REJECTED",
                from_status=old_status,
                to_status=quote.status,
                reason=reason,
                event_metadata={"step_id": step.id, "role": step.approval_role},
            )
            self.db.add(audit_evt)

        elif action == "RETURN":
            step.status = "RETURNED_FOR_REVISION"
            step.decided_by_user_id = current_user.id
            step.decision_reason = reason
            step.decided_at = now

            old_status = quote.status
            quote.status = QuotationStatus.RETURNED_FOR_REVISION.value

            audit_evt = QuoteAuditEvent(
                quotation_id=quote.id,
                actor_user_id=current_user.id,
                event_type="APPROVAL_RETURNED",
                from_status=old_status,
                to_status=quote.status,
                reason=reason,
                event_metadata={"step_id": step.id, "role": step.approval_role},
            )
            self.db.add(audit_evt)

        else:
            raise QuotationValidationError(f"Invalid approval action '{action}'.")

        try:
            await self.db.commit()
            res = await self.quote_repo.get_by_id(self.db, quote.id)
            if not res:
                raise ResourceNotFoundError("Quotation", quote.id)
            return res
        except Exception:
            await self.db.rollback()
            raise
