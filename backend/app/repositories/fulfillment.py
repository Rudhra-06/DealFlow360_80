from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.backorder import Backorder
from app.models.fulfillment_allocation import FulfillmentAllocation
from app.models.fulfillment_plan import FulfillmentPlan
from app.models.sales_order_line import SalesOrderLine
from app.models.warehouse import Warehouse
from app.repositories.base import BaseRepository


class FulfillmentPlanRepository(BaseRepository[FulfillmentPlan]):
    def __init__(self) -> None:
        super().__init__(FulfillmentPlan)

    def _default_options(self):
        return [
            selectinload(FulfillmentPlan.allocations).selectinload(FulfillmentAllocation.sales_order_line),
            selectinload(FulfillmentPlan.allocations).selectinload(FulfillmentAllocation.warehouse),
            selectinload(FulfillmentPlan.created_by_user),
        ]

    async def create_plan(self, db: AsyncSession, plan: FulfillmentPlan) -> FulfillmentPlan:
        db.add(plan)
        await db.flush()
        return plan

    async def get_active_plan_by_order(self, db: AsyncSession, sales_order_id: int) -> Optional[FulfillmentPlan]:
        stmt = (
            select(FulfillmentPlan)
            .options(*self._default_options())
            .where(FulfillmentPlan.sales_order_id == sales_order_id, FulfillmentPlan.status == "ACTIVE")
            .order_by(FulfillmentPlan.plan_version.desc())
            .limit(1)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_plans_by_order(self, db: AsyncSession, sales_order_id: int) -> List[FulfillmentPlan]:
        stmt = (
            select(FulfillmentPlan)
            .options(*self._default_options())
            .where(FulfillmentPlan.sales_order_id == sales_order_id)
            .order_by(FulfillmentPlan.plan_version.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())


class BackorderRepository(BaseRepository[Backorder]):
    def __init__(self) -> None:
        super().__init__(Backorder)

    def _default_options(self):
        return [
            selectinload(Backorder.sales_order_line).selectinload(SalesOrderLine.product),
        ]

    async def create_backorder(self, db: AsyncSession, backorder: Backorder) -> Backorder:
        db.add(backorder)
        await db.flush()
        return backorder

    async def list_open_by_order(self, db: AsyncSession, sales_order_id: int) -> List[Backorder]:
        stmt = (
            select(Backorder)
            .options(*self._default_options())
            .where(Backorder.sales_order_id == sales_order_id, Backorder.status.in_(["OPEN", "PARTIALLY_RESOLVED"]))
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def list_by_order(self, db: AsyncSession, sales_order_id: int) -> List[Backorder]:
        stmt = (
            select(Backorder)
            .options(*self._default_options())
            .where(Backorder.sales_order_id == sales_order_id)
            .order_by(Backorder.id.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
