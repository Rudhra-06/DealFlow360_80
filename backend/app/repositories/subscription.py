from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.billing_plan import BillingPlan
from app.models.billing_schedule import BillingSchedule
from app.models.customer import Customer
from app.models.sales_order import SalesOrder
from app.models.sales_order_line import SalesOrderLine
from app.models.subscription import Subscription
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    def __init__(self) -> None:
        super().__init__(Subscription)

    def _default_options(self):
        return [
            selectinload(Subscription.customer).selectinload(Customer.tier),
            selectinload(Subscription.sales_order),
            selectinload(Subscription.sales_order_line),
            selectinload(Subscription.billing_plan),
            selectinload(Subscription.schedules),
        ]

    async def create_subscription(self, db: AsyncSession, sub: Subscription) -> Subscription:
        db.add(sub)
        await db.flush()
        return sub

    async def get_by_id(self, db: AsyncSession, subscription_id: int) -> Optional[Subscription]:
        stmt = (
            select(Subscription)
            .options(*self._default_options())
            .execution_options(populate_existing=True)
            .where(Subscription.id == subscription_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_number(self, db: AsyncSession, subscription_number: str) -> Optional[Subscription]:
        stmt = select(Subscription).options(*self._default_options()).where(Subscription.subscription_number == subscription_number)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_order(self, db: AsyncSession, sales_order_id: int) -> List[Subscription]:
        stmt = (
            select(Subscription)
            .options(*self._default_options())
            .where(Subscription.sales_order_id == sales_order_id)
            .order_by(Subscription.id.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def list_subscriptions(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        sales_order_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Subscription]:
        stmt = select(Subscription).options(*self._default_options())

        if status is not None:
            stmt = stmt.where(Subscription.status == status)
        if customer_id is not None:
            stmt = stmt.where(Subscription.customer_id == customer_id)
        if sales_order_id is not None:
            stmt = stmt.where(Subscription.sales_order_id == sales_order_id)

        stmt = stmt.order_by(Subscription.created_at.desc()).offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def list_due_schedules(self, db: AsyncSession, as_of_date: datetime) -> List[BillingSchedule]:
        stmt = (
            select(BillingSchedule)
            .options(selectinload(BillingSchedule.subscription).selectinload(Subscription.sales_order_line))
            .where(
                BillingSchedule.status == "SCHEDULED",
                BillingSchedule.billing_date <= as_of_date,
            )
            .order_by(BillingSchedule.billing_date.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
