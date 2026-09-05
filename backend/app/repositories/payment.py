from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.payment_allocation import PaymentAllocation
from app.models.user import User
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self) -> None:
        super().__init__(Payment)

    def _default_options(self):
        return [
            selectinload(Payment.customer).selectinload(Customer.tier),
            selectinload(Payment.recorded_by_user).selectinload(User.role),
            selectinload(Payment.allocations).selectinload(PaymentAllocation.invoice),
        ]

    async def create_payment(self, db: AsyncSession, payment: Payment) -> Payment:
        db.add(payment)
        await db.flush()
        return payment

    async def get_by_id(self, db: AsyncSession, payment_id: int) -> Optional[Payment]:
        stmt = (
            select(Payment)
            .options(*self._default_options())
            .execution_options(populate_existing=True)
            .where(Payment.id == payment_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_number(self, db: AsyncSession, payment_number: str) -> Optional[Payment]:
        stmt = select(Payment).options(*self._default_options()).where(Payment.payment_number == payment_number)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_payments(
        self,
        db: AsyncSession,
        customer_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Payment]:
        stmt = select(Payment).options(*self._default_options())

        if customer_id is not None:
            stmt = stmt.where(Payment.customer_id == customer_id)
        if status is not None:
            stmt = stmt.where(Payment.status == status)

        stmt = stmt.order_by(Payment.created_at.desc()).offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())
