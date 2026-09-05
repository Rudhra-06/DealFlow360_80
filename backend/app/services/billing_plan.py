from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing_plan import BillingPlan
from app.repositories.billing_plan import BillingPlanRepository
from app.schemas.billing_plan import BillingPlanCreate, BillingPlanUpdate
from app.services.exceptions import (
    CommercialPolicyValidationError,
    DuplicateResourceError,
    ResourceNotFoundError,
)

ALLOWED_BILLING_TYPES = {"ONE_TIME", "RECURRING"}


class BillingPlanService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.plan_repo = BillingPlanRepository()

    async def _validate_plan_state(
        self,
        code: str,
        billing_type: str,
        billing_interval_months: Optional[int],
        payment_due_days: int,
        exclude_plan_id: Optional[int] = None,
    ) -> str:
        norm_code = code.strip().upper()
        if not norm_code:
            raise CommercialPolicyValidationError("BillingPlan code cannot be empty.")

        # 1. Duplicate code check
        existing = await self.plan_repo.get_by_code(self.db, norm_code)
        if existing and (exclude_plan_id is None or existing.id != exclude_plan_id):
            raise DuplicateResourceError(f"BillingPlan with code '{norm_code}' already exists.")

        # 2. Billing Type validation
        if billing_type not in ALLOWED_BILLING_TYPES:
            raise CommercialPolicyValidationError(
                f"billing_type '{billing_type}' is invalid. Allowed types: {sorted(list(ALLOWED_BILLING_TYPES))}."
            )

        # 3. Conditional Interval rules
        if billing_type == "ONE_TIME":
            if billing_interval_months is not None:
                raise CommercialPolicyValidationError("billing_interval_months must be null for ONE_TIME billing plans.")
        elif billing_type == "RECURRING":
            if billing_interval_months is None or billing_interval_months < 1:
                raise CommercialPolicyValidationError("billing_interval_months must be an integer >= 1 for RECURRING billing plans.")

        # 4. Payment terms due days check
        if payment_due_days < 0:
            raise CommercialPolicyValidationError("payment_due_days must be non-negative (>= 0).")

        return norm_code

    async def create_plan(self, obj_in: BillingPlanCreate) -> BillingPlan:
        try:
            norm_code = await self._validate_plan_state(
                code=obj_in.code,
                billing_type=obj_in.billing_type,
                billing_interval_months=obj_in.billing_interval_months,
                payment_due_days=obj_in.payment_due_days,
            )
            create_data = obj_in.model_dump()
            create_data["code"] = norm_code

            plan = BillingPlan(**create_data)
            self.db.add(plan)
            await self.db.flush()
            await self.db.commit()
            return await self.get_plan_by_id(plan.id)
        except Exception:
            await self.db.rollback()
            raise

    async def update_plan(self, plan_id: int, obj_in: BillingPlanUpdate) -> BillingPlan:
        plan = await self.plan_repo.get_by_id(self.db, plan_id)
        if not plan:
            raise ResourceNotFoundError(f"BillingPlan with ID {plan_id} not found.")

        patch_data = obj_in.model_dump(exclude_unset=True)

        final_code = patch_data.get("code", plan.code)
        final_type = patch_data.get("billing_type", plan.billing_type)
        
        # If switching type to ONE_TIME and interval not explicitly provided in patch, auto-null interval
        if final_type == "ONE_TIME" and "billing_interval_months" not in patch_data:
            final_interval = None
            patch_data["billing_interval_months"] = None
        else:
            final_interval = patch_data.get("billing_interval_months", plan.billing_interval_months)

        final_due_days = patch_data.get("payment_due_days", plan.payment_due_days)

        try:
            norm_code = await self._validate_plan_state(
                code=final_code,
                billing_type=final_type,
                billing_interval_months=final_interval,
                payment_due_days=final_due_days,
                exclude_plan_id=plan_id,
            )

            if "code" in patch_data:
                patch_data["code"] = norm_code

            for field, value in patch_data.items():
                setattr(plan, field, value)

            await self.db.flush()
            await self.db.commit()
            return await self.get_plan_by_id(plan_id)
        except Exception:
            await self.db.rollback()
            raise

    async def get_plan_by_id(self, plan_id: int) -> BillingPlan:
        plan = await self.plan_repo.get_by_id(self.db, plan_id)
        if not plan:
            raise ResourceNotFoundError(f"BillingPlan with ID {plan_id} not found.")
        return plan

    async def get_plan_by_code(self, code: str) -> BillingPlan:
        plan = await self.plan_repo.get_by_code(self.db, code.strip().upper())
        if not plan:
            raise ResourceNotFoundError(f"BillingPlan with code '{code}' not found.")
        return plan

    async def list_plans(
        self,
        billing_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[BillingPlan]:
        return await self.plan_repo.list_plans(
            self.db,
            billing_type=billing_type,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )
