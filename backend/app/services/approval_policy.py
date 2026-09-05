from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.roles import RoleName
from app.models.approval_policy import ApprovalPolicy
from app.repositories.approval_policy import ApprovalPolicyRepository
from app.repositories.customer_tier import CustomerTierRepository
from app.schemas.approval_policy import ApprovalPolicyCreate, ApprovalPolicyUpdate
from app.services.exceptions import (
    CommercialPolicyValidationError,
    InactiveReferenceError,
    InvalidReferenceError,
    ResourceNotFoundError,
)

ALLOWED_APPROVAL_ROLES = {RoleName.SALES_MANAGER, RoleName.FINANCE_OPERATIONS}


class ApprovalPolicyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.policy_repo = ApprovalPolicyRepository()
        self.tier_repo = CustomerTierRepository()

    async def _validate_policy_state(
        self,
        name: str,
        customer_tier_id: Optional[int],
        discount_above_pct: Optional[Decimal],
        margin_below_pct: Optional[Decimal],
        payment_terms_above_days: Optional[int],
        blended_risk_above: Optional[Decimal],
        approval_role: str,
        priority: int,
        effective_from: datetime,
        effective_to: Optional[datetime],
        is_active: bool,
    ) -> None:
        # 1. Operational Approver Role validation
        if approval_role not in ALLOWED_APPROVAL_ROLES:
            raise CommercialPolicyValidationError(
                f"approval_role '{approval_role}' is not allowed. Allowed operational approval roles: {sorted(list(ALLOWED_APPROVAL_ROLES))}."
            )

        # 2. At least one trigger requirement
        if discount_above_pct is None and margin_below_pct is None and payment_terms_above_days is None and blended_risk_above is None:
            raise CommercialPolicyValidationError(
                "ApprovalPolicy must specify at least one threshold trigger (discount_above_pct, margin_below_pct, payment_terms_above_days, or blended_risk_above)."
            )

        # 3. Threshold bounds validation
        if discount_above_pct is not None:
            if discount_above_pct < Decimal("0.00") or discount_above_pct > Decimal("100.00"):
                raise CommercialPolicyValidationError("discount_above_pct must be between 0.00 and 100.00.")

        if margin_below_pct is not None:
            if margin_below_pct < Decimal("-100.00") or margin_below_pct > Decimal("100.00"):
                raise CommercialPolicyValidationError("margin_below_pct must be between -100.00 and 100.00.")

        if payment_terms_above_days is not None:
            if payment_terms_above_days < 0:
                raise CommercialPolicyValidationError("payment_terms_above_days must be non-negative (>= 0).")

        if blended_risk_above is not None:
            if blended_risk_above < Decimal("0.00") or blended_risk_above > Decimal("100.00"):
                raise CommercialPolicyValidationError("blended_risk_above must be between 0.00 and 100.00.")

        # 4. Effective date ordering check
        if effective_to is not None and effective_to <= effective_from:
            raise CommercialPolicyValidationError("effective_to timestamp must be strictly after effective_from timestamp.")

        # 5. Active Foreign Reference Check
        if customer_tier_id is not None:
            tier = await self.tier_repo.get_by_id(self.db, customer_tier_id)
            if not tier:
                raise InvalidReferenceError(f"CustomerTier with ID {customer_tier_id} does not exist.")
            if not tier.is_active:
                raise InactiveReferenceError(f"CustomerTier '{tier.name}' (ID {customer_tier_id}) is inactive.")

    async def create_policy(self, obj_in: ApprovalPolicyCreate) -> ApprovalPolicy:
        try:
            eff_from = obj_in.effective_from or datetime.now(timezone.utc)
            await self._validate_policy_state(
                name=obj_in.name,
                customer_tier_id=obj_in.customer_tier_id,
                discount_above_pct=obj_in.discount_above_pct,
                margin_below_pct=obj_in.margin_below_pct,
                payment_terms_above_days=obj_in.payment_terms_above_days,
                blended_risk_above=obj_in.blended_risk_above,
                approval_role=obj_in.approval_role,
                priority=obj_in.priority,
                effective_from=eff_from,
                effective_to=obj_in.effective_to,
                is_active=obj_in.is_active,
            )
            create_data = obj_in.model_dump()
            create_data["effective_from"] = eff_from

            policy = ApprovalPolicy(**create_data)
            self.db.add(policy)
            await self.db.flush()
            await self.db.commit()
            return await self.get_policy_by_id(policy.id)
        except Exception:
            await self.db.rollback()
            raise

    async def update_policy(self, policy_id: int, obj_in: ApprovalPolicyUpdate) -> ApprovalPolicy:
        policy = await self.policy_repo.get_by_id(self.db, policy_id)
        if not policy:
            raise ResourceNotFoundError(f"ApprovalPolicy with ID {policy_id} not found.")

        patch_data = obj_in.model_dump(exclude_unset=True)

        final_name = patch_data.get("name", policy.name)
        final_tier_id = patch_data.get("customer_tier_id", policy.customer_tier_id)
        final_disc_above = patch_data.get("discount_above_pct", policy.discount_above_pct)
        final_margin_below = patch_data.get("margin_below_pct", policy.margin_below_pct)
        final_terms_above = patch_data.get("payment_terms_above_days", policy.payment_terms_above_days)
        final_risk_above = patch_data.get("blended_risk_above", policy.blended_risk_above)
        final_role = patch_data.get("approval_role", policy.approval_role)
        final_priority = patch_data.get("priority", policy.priority)
        final_eff_from = patch_data.get("effective_from", policy.effective_from)
        final_eff_to = patch_data.get("effective_to", policy.effective_to)
        final_is_active = patch_data.get("is_active", policy.is_active)

        try:
            await self._validate_policy_state(
                name=final_name,
                customer_tier_id=final_tier_id,
                discount_above_pct=final_disc_above,
                margin_below_pct=final_margin_below,
                payment_terms_above_days=final_terms_above,
                blended_risk_above=final_risk_above,
                approval_role=final_role,
                priority=final_priority,
                effective_from=final_eff_from,
                effective_to=final_eff_to,
                is_active=final_is_active,
            )

            for field, value in patch_data.items():
                setattr(policy, field, value)

            await self.db.flush()
            await self.db.commit()
            return await self.get_policy_by_id(policy_id)
        except Exception:
            await self.db.rollback()
            raise

    async def get_policy_by_id(self, policy_id: int) -> ApprovalPolicy:
        policy = await self.policy_repo.get_by_id(self.db, policy_id)
        if not policy:
            raise ResourceNotFoundError(f"ApprovalPolicy with ID {policy_id} not found.")
        return policy

    async def list_policies(
        self,
        customer_tier_id: Optional[int] = None,
        approval_role: Optional[str] = None,
        is_active: Optional[bool] = None,
        effective_only: bool = False,
        as_of: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ApprovalPolicy]:
        return await self.policy_repo.list_policies(
            self.db,
            customer_tier_id=customer_tier_id,
            approval_role=approval_role,
            is_active=is_active,
            effective_only=effective_only,
            as_of=as_of,
            limit=limit,
            offset=offset,
        )
