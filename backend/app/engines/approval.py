from decimal import Decimal
from typing import List, Optional, Sequence
from pydantic import BaseModel

from app.core.enums import QuotationStatus, RoleName


class ApprovalTriggerDetail(BaseModel):
    approval_policy_id: Optional[int] = None
    trigger_code: str
    approval_role: str
    actual_value: Optional[Decimal] = None
    threshold_value: Optional[Decimal] = None
    message: str


class ApprovalEvaluationResult(BaseModel):
    requires_approval: bool
    required_roles: List[str]
    projected_status: QuotationStatus
    triggers: List[ApprovalTriggerDetail]


class ApprovalEngine:
    """Deterministic, side-effect free approval policy evaluation engine."""

    @classmethod
    def evaluate(
        cls,
        weighted_effective_discount_pct: Decimal,
        margin_pct: Decimal,
        payment_terms_days: int,
        blended_risk_score: Decimal,
        customer_tier_id: Optional[int],
        has_line_over_max_discount: bool,
        active_policies: Sequence[dict],
    ) -> ApprovalEvaluationResult:
        triggers: List[ApprovalTriggerDetail] = []
        roles_needed = set()

        # 1. Line-level ceiling violation check (requires Sales Manager at minimum)
        if has_line_over_max_discount:
            roles_needed.add(RoleName.SALES_MANAGER)
            triggers.append(
                ApprovalTriggerDetail(
                    approval_policy_id=None,
                    trigger_code="LINE_DISCOUNT_ABOVE_MAX",
                    approval_role=RoleName.SALES_MANAGER,
                    actual_value=None,
                    threshold_value=None,
                    message="At least one product line exceeds the maximum policy discount ceiling.",
                )
            )

        # 2. Evaluate configurable Approval Policies (AND within policy, OR across policies)
        for policy in active_policies:
            # Tier matching check
            p_tier_id = policy.get("customer_tier_id")
            if p_tier_id is not None and p_tier_id != customer_tier_id:
                continue

            disc_above = policy.get("discount_above_pct")
            margin_below = policy.get("margin_below_pct")
            terms_above = policy.get("payment_terms_above_days")
            risk_above = policy.get("blended_risk_above")

            # Must have at least one trigger defined
            has_definition = any(x is not None for x in (disc_above, margin_below, terms_above, risk_above))
            if not has_definition:
                continue

            breached_all = True
            policy_triggers: List[ApprovalTriggerDetail] = []

            if disc_above is not None:
                if weighted_effective_discount_pct > disc_above:
                    policy_triggers.append(
                        ApprovalTriggerDetail(
                            approval_policy_id=policy.get("id"),
                            trigger_code="DISCOUNT_THRESHOLD",
                            approval_role=policy["approval_role"],
                            actual_value=weighted_effective_discount_pct,
                            threshold_value=disc_above,
                            message=f"Effective quotation discount ({weighted_effective_discount_pct}%) exceeds approval threshold ({disc_above}%).",
                        )
                    )
                else:
                    breached_all = False

            if margin_below is not None:
                if margin_pct < margin_below:
                    policy_triggers.append(
                        ApprovalTriggerDetail(
                            approval_policy_id=policy.get("id"),
                            trigger_code="MARGIN_THRESHOLD",
                            approval_role=policy["approval_role"],
                            actual_value=margin_pct,
                            threshold_value=margin_below,
                            message=f"Quotation margin ({margin_pct}%) is below approval threshold ({margin_below}%).",
                        )
                    )
                else:
                    breached_all = False

            if terms_above is not None:
                if payment_terms_days > terms_above:
                    policy_triggers.append(
                        ApprovalTriggerDetail(
                            approval_policy_id=policy.get("id"),
                            trigger_code="PAYMENT_TERMS_THRESHOLD",
                            approval_role=policy["approval_role"],
                            actual_value=Decimal(payment_terms_days),
                            threshold_value=Decimal(terms_above),
                            message=f"Payment terms ({payment_terms_days} days) exceed approval threshold ({terms_above} days).",
                        )
                    )
                else:
                    breached_all = False

            if risk_above is not None:
                if blended_risk_score > risk_above:
                    policy_triggers.append(
                        ApprovalTriggerDetail(
                            approval_policy_id=policy.get("id"),
                            trigger_code="BLENDED_RISK_THRESHOLD",
                            approval_role=policy["approval_role"],
                            actual_value=blended_risk_score,
                            threshold_value=risk_above,
                            message=f"Blended risk score ({blended_risk_score}) exceeds approval threshold ({risk_above}).",
                        )
                    )
                else:
                    breached_all = False

            # If ALL specified triggers on this policy were breached, record triggers & required role
            if breached_all and policy_triggers:
                roles_needed.add(policy["approval_role"])
                triggers.extend(policy_triggers)

        # 3. Determine sequential approval chain & projected status
        if not roles_needed:
            return ApprovalEvaluationResult(
                requires_approval=False,
                required_roles=[],
                projected_status=QuotationStatus.APPROVED,
                triggers=[],
            )

        if RoleName.FINANCE_OPERATIONS in roles_needed:
            # Finance requires 2-level chain: Sales Manager -> Finance
            chain = [RoleName.SALES_MANAGER, RoleName.FINANCE_OPERATIONS]
            proj_status = QuotationStatus.PENDING_MANAGER_APPROVAL
        else:
            chain = [RoleName.SALES_MANAGER]
            proj_status = QuotationStatus.PENDING_MANAGER_APPROVAL

        return ApprovalEvaluationResult(
            requires_approval=True,
            required_roles=chain,
            projected_status=proj_status,
            triggers=triggers,
        )
