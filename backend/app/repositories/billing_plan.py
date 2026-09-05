from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing_plan import BillingPlan
from app.repositories.base import BaseRepository
from app.schemas.billing_plan import BillingPlanCreate


class BillingPlanRepository(BaseRepository[BillingPlan]):
    def __init__(self):
        super().__init__(BillingPlan)

    async def create_plan(
        self, db: AsyncSession, obj_in: BillingPlanCreate
    ) -> BillingPlan:
        plan = BillingPlan(**obj_in.model_dump())
        db.add(plan)
        await db.flush()
        return plan

    async def get_by_id(self, db: AsyncSession, plan_id: int) -> Optional[BillingPlan]:
        stmt = select(BillingPlan).where(BillingPlan.id == plan_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[BillingPlan]:
        stmt = select(BillingPlan).where(BillingPlan.code == code)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_plans(
        self,
        db: AsyncSession,
        billing_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[BillingPlan]:
        stmt = select(BillingPlan)
        filters = []

        if billing_type is not None:
            filters.append(BillingPlan.billing_type == billing_type)
        if is_active is not None:
            filters.append(BillingPlan.is_active == is_active)

        if filters:
            stmt = stmt.where(*filters)

        stmt = stmt.order_by(BillingPlan.code.asc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
