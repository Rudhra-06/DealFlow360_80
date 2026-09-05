from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AuditEventType, NotificationType, QuotationStatus, RoleName
from app.engines.approval import ApprovalEngine
from app.models.quotation import Quotation
from app.models.quote_approval_step import QuoteApprovalStep
from app.models.quote_approval_trigger import QuoteApprovalTrigger
from app.models.quote_audit_event import QuoteAuditEvent
from app.models.quote_negotiation_line_change import QuoteNegotiationLineChange
from app.models.quote_negotiation_message import QuoteNegotiationMessage
from app.models.quote_negotiation_request import QuoteNegotiationRequest
from app.models.user import User
from app.repositories.approval_policy import ApprovalPolicyRepository
from app.repositories.customer_portal_access import CustomerPortalAccessRepository
from app.repositories.quotation import QuotationRepository
from app.repositories.quote_approval_step import QuoteApprovalStepRepository
from app.repositories.quote_negotiation import QuoteNegotiationMessageRepository, QuoteNegotiationRequestRepository
from app.repositories.quote_version import QuoteVersionRepository
from app.repositories.user import UserRepository
from app.schemas.quote_negotiation import (
    QuoteNegotiationMessageCreate,
    QuoteNegotiationRequestCreate,
    QuoteNegotiationRequestReject,
)
from app.services.exceptions import (
    CommercialPolicyValidationError,
    InvalidReferenceError,
    QuoteAccessDeniedError,
    QuoteNotFoundError,
    ResourceNotFoundError,
)
from app.services.notification import NotificationService
from app.services.quotation_evaluation import QuotationEvaluationService
from app.services.quote_version import QuoteVersionService


class QuoteNegotiationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.quote_repo = QuotationRepository()
        self.msg_repo = QuoteNegotiationMessageRepository()
        self.req_repo = QuoteNegotiationRequestRepository()
        self.version_service = QuoteVersionService(db)
        self.version_repo = QuoteVersionRepository()
        self.eval_service = QuotationEvaluationService(db)
        self.step_repo = QuoteApprovalStepRepository()
        self.policy_repo = ApprovalPolicyRepository()
        self.portal_access_repo = CustomerPortalAccessRepository()
        self.notif_service = NotificationService(db)
        self.user_repo = UserRepository()

    async def add_customer_message(
        self, quotation_id: int, obj_in: QuoteNegotiationMessageCreate, current_user: User
    ) -> QuoteNegotiationMessage:
        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")

        # Ensure customer user is associated with quote's customer
        access = await self.portal_access_repo.get_active_by_user_id(self.db, current_user.id)
        if not access or access.customer_id != quote.customer_id:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")

        if quote.status not in {QuotationStatus.SENT_TO_CUSTOMER.value, QuotationStatus.UNDER_NEGOTIATION.value}:
            raise CommercialPolicyValidationError(f"Cannot post messages while quotation is in '{quote.status}' status.")

        try:
            if quote.status == QuotationStatus.SENT_TO_CUSTOMER.value:
                quote.status = QuotationStatus.UNDER_NEGOTIATION.value
                self.db.add(
                    QuoteAuditEvent(
                        quotation_id=quote.id,
                        actor_user_id=current_user.id,
                        event_type=AuditEventType.NEGOTIATION_STARTED.value,
                        from_status=QuotationStatus.SENT_TO_CUSTOMER.value,
                        to_status=QuotationStatus.UNDER_NEGOTIATION.value,
                    )
                )

            current_ver = await self.version_repo.get_latest_version(self.db, quote.id)
            version_id = current_ver.id if current_ver else None

            msg = QuoteNegotiationMessage(
                quotation_id=quote.id,
                quote_version_id=version_id,
                quotation_line_id=obj_in.quotation_line_id,
                author_user_id=current_user.id,
                message_type=obj_in.message_type or "COMMENT",
                message=obj_in.message,
                is_customer_visible=True,
            )
            await self.msg_repo.create_message(self.db, msg)

            self.db.add(
                QuoteAuditEvent(
                    quotation_id=quote.id,
                    actor_user_id=current_user.id,
                    event_type=AuditEventType.CUSTOMER_COMMENT_ADDED.value,
                    to_status=quote.status,
                    event_metadata={"message_type": msg.message_type, "line_id": obj_in.quotation_line_id},
                )
            )

            # Persist notification for Sales Rep
            await self.notif_service.create_notification_record(
                user_id=quote.sales_rep_id,
                notification_type=NotificationType.CUSTOMER_COMMENT.value,
                title=f"New Message on Quote {quote.quote_number}",
                message=f"Customer posted a {msg.message_type}: '{obj_in.message[:100]}...'",
                quotation_id=quote.id,
            )

            await self.db.commit()

            # Post-commit real-time event
            await self.notif_service.dispatch_post_commit_events(
                target_user_ids=[quote.sales_rep_id],
                event_name="negotiation.message_created",
                quotation_id=quote.id,
                payload={"message_id": msg.id, "message": obj_in.message, "author_id": current_user.id},
                title=f"New Message on Quote {quote.quote_number}",
                message_text=f"Customer posted a {msg.message_type}.",
            )

            return msg
        except Exception:
            await self.db.rollback()
            raise

    async def add_internal_message(
        self, quotation_id: int, obj_in: QuoteNegotiationMessageCreate, current_user: User
    ) -> QuoteNegotiationMessage:
        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")

        current_ver = await self.version_repo.get_latest_version(self.db, quote.id)
        version_id = current_ver.id if current_ver else None

        try:
            msg = QuoteNegotiationMessage(
                quotation_id=quote.id,
                quote_version_id=version_id,
                quotation_line_id=obj_in.quotation_line_id,
                author_user_id=current_user.id,
                message_type="INTERNAL_REPLY",
                message=obj_in.message,
                is_customer_visible=True,
            )
            await self.msg_repo.create_message(self.db, msg)

            # Target portal users for notification
            portal_accesses = await self.portal_access_repo.list_access(self.db, customer_id=quote.customer_id, is_active=True)
            cust_user_ids = [pa.user_id for pa in portal_accesses]

            for uid in cust_user_ids:
                await self.notif_service.create_notification_record(
                    user_id=uid,
                    notification_type=NotificationType.CUSTOMER_COMMENT.value,
                    title=f"Sales Reply on Quote {quote.quote_number}",
                    message=f"Sales Rep replied: '{obj_in.message[:100]}...'",
                    quotation_id=quote.id,
                )

            await self.db.commit()

            # Post-commit real-time event
            await self.notif_service.dispatch_post_commit_events(
                target_user_ids=cust_user_ids,
                event_name="negotiation.message_created",
                quotation_id=quote.id,
                payload={"message_id": msg.id, "message": obj_in.message, "author_id": current_user.id},
                title=f"Sales Reply on Quote {quote.quote_number}",
                message_text="Sales Rep replied to your quotation message.",
            )

            return msg
        except Exception:
            await self.db.rollback()
            raise

    async def submit_counter_offer(
        self, quotation_id: int, obj_in: QuoteNegotiationRequestCreate, current_user: User
    ) -> QuoteNegotiationRequest:
        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")

        # Ensure customer user mapping
        access = await self.portal_access_repo.get_active_by_user_id(self.db, current_user.id)
        if not access or access.customer_id != quote.customer_id:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")

        if quote.status not in {QuotationStatus.SENT_TO_CUSTOMER.value, QuotationStatus.UNDER_NEGOTIATION.value}:
            raise CommercialPolicyValidationError(f"Cannot submit counter-offer while quote is in '{quote.status}' status.")

        # Validate base version against current version
        latest_ver = await self.version_repo.get_latest_version(self.db, quote.id)
        if not latest_ver:
            raise CommercialPolicyValidationError("Quotation does not have an active published version.")

        # Stale version check
        base_ver_num = latest_ver.version_number

        # Require at least one meaningful requested change
        has_change = (
            obj_in.requested_order_discount_pct is not None
            or obj_in.requested_payment_terms_days is not None
            or len(obj_in.line_changes) > 0
            or (obj_in.message and obj_in.message.strip())
        )
        if not has_change:
            raise CommercialPolicyValidationError("Negotiation request must contain at least one proposed commercial change or message.")

        # Validate line ownership
        quote_line_ids = {l.id for l in quote.lines}
        for lc in obj_in.line_changes:
            if lc.quotation_line_id not in quote_line_ids:
                raise InvalidReferenceError(f"Line ID {lc.quotation_line_id} does not belong to quotation {quote.id}.")

        try:
            if quote.status == QuotationStatus.SENT_TO_CUSTOMER.value:
                quote.status = QuotationStatus.UNDER_NEGOTIATION.value

            req = QuoteNegotiationRequest(
                quotation_id=quote.id,
                base_quote_version_id=latest_ver.id,
                requested_by_user_id=current_user.id,
                request_type=obj_in.request_type,
                status="PENDING",
                message=obj_in.message,
                requested_order_discount_pct=obj_in.requested_order_discount_pct,
                requested_payment_terms_days=obj_in.requested_payment_terms_days,
            )

            for lc in obj_in.line_changes:
                req.line_changes.append(
                    QuoteNegotiationLineChange(
                        quotation_line_id=lc.quotation_line_id,
                        requested_quantity=lc.requested_quantity,
                        requested_line_discount_pct=lc.requested_line_discount_pct,
                    )
                )

            await self.req_repo.create_request(self.db, req)

            self.db.add(
                QuoteAuditEvent(
                    quotation_id=quote.id,
                    actor_user_id=current_user.id,
                    event_type=AuditEventType.CUSTOMER_COUNTER_OFFERED.value,
                    to_status=quote.status,
                    event_metadata={"request_id": req.id, "base_version": base_ver_num, "request_type": req.request_type},
                )
            )

            # Persist notification for Sales Rep
            await self.notif_service.create_notification_record(
                user_id=quote.sales_rep_id,
                notification_type=NotificationType.CUSTOMER_COUNTER_OFFER.value,
                title=f"New Counter-Offer on Quote {quote.quote_number}",
                message=f"Customer submitted a {req.request_type} against Version {base_ver_num}.",
                quotation_id=quote.id,
                payload={"request_id": req.id},
            )

            await self.db.commit()

            # Post-commit real-time dispatch
            await self.notif_service.dispatch_post_commit_events(
                target_user_ids=[quote.sales_rep_id],
                event_name="negotiation.requested",
                quotation_id=quote.id,
                payload={"request_id": req.id, "request_type": req.request_type, "base_version": base_ver_num},
                title=f"New Counter-Offer on Quote {quote.quote_number}",
                message_text="Customer submitted a counter-offer.",
            )

            return await self.req_repo.get_by_id(self.db, req.id)
        except Exception:
            await self.db.rollback()
            raise

    async def accept_negotiation_request(self, quotation_id: int, request_id: int, current_user: User) -> Quotation:
        """ATOMIC ACCEPTANCE TRANSACTION: Applies counter-offer, recalculates quote, runs ApprovalEngine, snapshots new version, and routes for reapproval or customer return."""
        # 1. Lock quotation and negotiation request
        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")

        # RBAC check
        is_admin = hasattr(current_user, "role") and current_user.role and current_user.role.name == RoleName.ADMIN
        if not is_admin and quote.sales_rep_id != current_user.id:
            raise QuoteAccessDeniedError("Only the assigned Sales Rep or Admin can resolve negotiation requests.")

        req = await self.req_repo.get_by_id(self.db, request_id)
        if not req or req.quotation_id != quotation_id:
            raise ResourceNotFoundError(f"NegotiationRequest ID {request_id} not found for quote {quotation_id}.")

        if req.status != "PENDING":
            raise CommercialPolicyValidationError(f"NegotiationRequest {request_id} is in '{req.status}' status and cannot be accepted.")

        # Stale version check: base version must match current quote version
        current_ver = await self.version_repo.get_latest_version(self.db, quote.id)
        if current_ver and req.base_quote_version_id != current_ver.id:
            raise CommercialPolicyValidationError(
                f"NegotiationRequest {request_id} was submitted against stale Version {req.base_version.version_number}. Current quote version is v{current_ver.version_number}."
            )

        try:
            # 2. Apply requested commercial modifications
            if req.requested_order_discount_pct is not None:
                quote.order_discount_pct = req.requested_order_discount_pct
            if req.requested_payment_terms_days is not None:
                quote.payment_terms_days = req.requested_payment_terms_days

            lines_by_id = {l.id: l for l in quote.lines}
            for lc in req.line_changes:
                line = lines_by_id.get(lc.quotation_line_id)
                if line:
                    if lc.requested_quantity is not None:
                        line.quantity = lc.requested_quantity
                    if lc.requested_line_discount_pct is not None:
                        line.line_discount_pct = lc.requested_line_discount_pct

            # 3. Recalculate quotation (Pricing, Margin, Risk, Policy snapshots)
            await self.eval_service.evaluate_and_update(quote)

            # 4. Evaluate ApprovalEngine
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

            eval_res = ApprovalEngine.evaluate(
                weighted_effective_discount_pct=quote.weighted_effective_discount_pct,
                margin_pct=quote.margin_pct,
                payment_terms_days=quote.payment_terms_days,
                blended_risk_score=quote.blended_risk_score,
                customer_tier_id=customer_tier_id,
                has_line_over_max_discount=has_line_over_max,
                active_policies=active_policies,
            )

            now = datetime.now(timezone.utc)
            req.status = "ACCEPTED"
            req.resolved_at = now
            req.resolved_by_user_id = current_user.id
            req.resolution_reason = "Accepted by Sales Rep."

            # Supersede older pending requests on same quotation
            await self.req_repo.supersede_older_pending_requests(self.db, quote.id, req.id)

            target_user_ids = []

            # 5. Check if reapproval is required
            if eval_res.requires_approval:
                # Needs reapproval -> create new approval round
                current_round = await self.step_repo.get_latest_round(self.db, quote.id) + 1
                for seq, role_name in enumerate(eval_res.required_roles, start=1):
                    step = QuoteApprovalStep(
                        quotation_id=quote.id,
                        approval_round=current_round,
                        sequence=seq,
                        approval_role=role_name,
                        approval_context="NEGOTIATION",
                        status="PENDING",
                        requested_at=now,
                    )
                    await self.step_repo.create_step(self.db, step)

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

                quote.status = QuotationStatus.REAPPROVAL_REQUIRED.value
                # Immediately move to first approval state (e.g. PENDING_MANAGER_APPROVAL)
                quote.status = eval_res.projected_status.value
                await self.db.flush()

                # Snapshot Version N+1 with PENDING approval status
                new_ver = await self.version_service.create_version_snapshot(
                    quotation_id=quote.id,
                    source_type="CUSTOMER_COUNTER_ACCEPTED",
                    created_by_user_id=current_user.id,
                    source_negotiation_request_id=req.id,
                    approval_status="PENDING_APPROVAL",
                )

                self.db.add(
                    QuoteAuditEvent(
                        quotation_id=quote.id,
                        actor_user_id=current_user.id,
                        event_type=AuditEventType.REAPPROVAL_REQUIRED.value,
                        to_status=quote.status,
                        event_metadata={"request_id": req.id, "version_id": new_ver.id},
                    )
                )

                # Fetch users with first approval role for notification
                first_role = eval_res.required_roles[0]
                approver_users = await self.user_repo.list_users(self.db)
                target_user_ids = [u.id for u in approver_users if u.role and u.role.name == first_role]

                for uid in target_user_ids:
                    await self.notif_service.create_notification_record(
                        user_id=uid,
                        notification_type=NotificationType.APPROVAL_REQUIRED.value,
                        title=f"Reapproval Required: Quote {quote.quote_number}",
                        message=f"Negotiated terms on Quote {quote.quote_number} require {first_role} approval.",
                        quotation_id=quote.id,
                    )
            else:
                # No reapproval required -> return quote to customer
                quote.status = QuotationStatus.SENT_TO_CUSTOMER.value
                await self.db.flush()

                new_ver = await self.version_service.create_version_snapshot(
                    quotation_id=quote.id,
                    source_type="CUSTOMER_COUNTER_ACCEPTED",
                    created_by_user_id=current_user.id,
                    source_negotiation_request_id=req.id,
                    approval_status="APPROVED",
                )

                self.db.add(
                    QuoteAuditEvent(
                        quotation_id=quote.id,
                        actor_user_id=current_user.id,
                        event_type=AuditEventType.NEGOTIATION_TERMS_APPLIED.value,
                        to_status=QuotationStatus.SENT_TO_CUSTOMER.value,
                        event_metadata={"request_id": req.id, "version_id": new_ver.id},
                    )
                )

                portal_accesses = await self.portal_access_repo.list_access(self.db, customer_id=quote.customer_id, is_active=True)
                target_user_ids = [pa.user_id for pa in portal_accesses]

                for uid in target_user_ids:
                    await self.notif_service.create_notification_record(
                        user_id=uid,
                        notification_type=NotificationType.NEGOTIATION_ACCEPTED.value,
                        title=f"Counter-Offer Accepted: Quote {quote.quote_number}",
                        message=f"Sales Rep accepted your counter-offer. Revised Version {new_ver.version_number} is ready for review.",
                        quotation_id=quote.id,
                    )

            await self.db.commit()

            # 6. Post-commit real-time broadcast
            event_name = "approval.required" if eval_res.requires_approval else "negotiation.accepted"
            await self.notif_service.dispatch_post_commit_events(
                target_user_ids=target_user_ids,
                event_name=event_name,
                quotation_id=quote.id,
                payload={"version_number": new_ver.version_number, "status": quote.status, "request_id": req.id},
                title=f"Quote {quote.quote_number} Updated",
                message_text=f"Negotiation request accepted. Status: {quote.status}.",
            )

            return await self.quote_repo.get_by_id(self.db, quote.id)
        except Exception:
            await self.db.rollback()
            raise

    async def reject_negotiation_request(
        self, quotation_id: int, request_id: int, obj_in: QuoteNegotiationRequestReject, current_user: User
    ) -> QuoteNegotiationRequest:
        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")

        is_admin = hasattr(current_user, "role") and current_user.role and current_user.role.name == RoleName.ADMIN
        if not is_admin and quote.sales_rep_id != current_user.id:
            raise QuoteAccessDeniedError("Only the assigned Sales Rep or Admin can resolve negotiation requests.")

        req = await self.req_repo.get_by_id(self.db, request_id)
        if not req or req.quotation_id != quotation_id:
            raise ResourceNotFoundError(f"NegotiationRequest ID {request_id} not found for quote {quotation_id}.")

        if req.status != "PENDING":
            raise CommercialPolicyValidationError(f"NegotiationRequest {request_id} is in '{req.status}' status and cannot be rejected.")

        try:
            now = datetime.now(timezone.utc)
            req.status = "REJECTED"
            req.resolved_at = now
            req.resolved_by_user_id = current_user.id
            req.resolution_reason = obj_in.resolution_reason or obj_in.rejection_reason or "Rejected"

            # Check remaining pending requests
            pending_other = await self.req_repo.get_pending_by_quote(self.db, quote.id)
            if not pending_other:
                quote.status = QuotationStatus.SENT_TO_CUSTOMER.value

            self.db.add(
                QuoteAuditEvent(
                    quotation_id=quote.id,
                    actor_user_id=current_user.id,
                    event_type=AuditEventType.NEGOTIATION_REQUEST_REJECTED.value,
                    to_status=quote.status,
                    reason=obj_in.resolution_reason,
                    event_metadata={"request_id": req.id},
                )
            )

            portal_accesses = await self.portal_access_repo.list_access(self.db, customer_id=quote.customer_id, is_active=True)
            cust_user_ids = [pa.user_id for pa in portal_accesses]

            for uid in cust_user_ids:
                await self.notif_service.create_notification_record(
                    user_id=uid,
                    notification_type=NotificationType.NEGOTIATION_REJECTED.value,
                    title=f"Counter-Offer Declined: Quote {quote.quote_number}",
                    message=f"Sales Rep declined your request: '{obj_in.resolution_reason}'",
                    quotation_id=quote.id,
                )

            await self.db.commit()

            # Post-commit real-time dispatch
            await self.notif_service.dispatch_post_commit_events(
                target_user_ids=cust_user_ids,
                event_name="negotiation.rejected",
                quotation_id=quote.id,
                payload={"request_id": req.id, "reason": obj_in.resolution_reason},
                title=f"Counter-Offer Declined: Quote {quote.quote_number}",
                message_text="Counter-offer declined by Sales Rep.",
            )

            return await self.req_repo.get_by_id(self.db, req.id)
        except Exception:
            await self.db.rollback()
            raise

    async def withdraw_negotiation_request(self, quotation_id: int, request_id: int, current_user: User) -> QuoteNegotiationRequest:
        req = await self.req_repo.get_by_id(self.db, request_id)
        if not req or req.quotation_id != quotation_id:
            raise ResourceNotFoundError(f"NegotiationRequest {request_id} not found.")

        if req.requested_by_user_id != current_user.id:
            raise QuoteAccessDeniedError("Only the user who created this request can withdraw it.")

        if req.status != "PENDING":
            raise CommercialPolicyValidationError(f"NegotiationRequest {request_id} is in '{req.status}' status and cannot be withdrawn.")

        try:
            req.status = "WITHDRAWN"
            req.resolved_at = datetime.now(timezone.utc)
            req.resolved_by_user_id = current_user.id
            req.resolution_reason = "Withdrawn by customer."

            self.db.add(
                QuoteAuditEvent(
                    quotation_id=quotation_id,
                    actor_user_id=current_user.id,
                    event_type=AuditEventType.CUSTOMER_REQUEST_WITHDRAWN.value,
                    event_metadata={"request_id": req.id},
                )
            )

            await self.db.commit()
            return await self.req_repo.get_by_id(self.db, req.id)
        except Exception:
            await self.db.rollback()
            raise

    async def get_negotiation_inbox(self, quotation_id: int) -> List[QuoteNegotiationRequest]:
        """Canonical method to query negotiation requests for a quotation inbox."""
        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")
        return await self.req_repo.list_requests(self.db, quotation_id)

