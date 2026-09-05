from typing import List, Optional
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.sales_order import SalesOrder
from app.models.sales_order_line import SalesOrderLine
from app.models.user import User
from app.repositories.base import BaseRepository


class SalesOrderRepository(BaseRepository[SalesOrder]):
    def __init__(self) -> None:
        super().__init__(SalesOrder)

    def _default_options(self):
        return [
            selectinload(SalesOrder.customer).selectinload(Customer.tier),
            selectinload(SalesOrder.sales_rep).selectinload(User.role),
            selectinload(SalesOrder.quotation),
            selectinload(SalesOrder.confirmed_quote_version),
            selectinload(SalesOrder.lines).selectinload(SalesOrderLine.product),
            selectinload(SalesOrder.lines).selectinload(SalesOrderLine.billing_plan),
        ]

    async def create_order(self, db: AsyncSession, order: SalesOrder) -> SalesOrder:
        db.add(order)
        await db.flush()
        return order

    async def get_by_id(self, db: AsyncSession, order_id: int) -> Optional[SalesOrder]:
        stmt = (
            select(SalesOrder)
            .options(*self._default_options())
            .execution_options(populate_existing=True)
            .where(SalesOrder.id == order_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_order_number(self, db: AsyncSession, order_number: str) -> Optional[SalesOrder]:
        stmt = select(SalesOrder).options(*self._default_options()).where(SalesOrder.order_number == order_number)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_quotation_id(self, db: AsyncSession, quotation_id: int) -> Optional[SalesOrder]:
        stmt = select(SalesOrder).options(*self._default_options()).where(SalesOrder.quotation_id == quotation_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_orders(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        sales_rep_id: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SalesOrder]:
        stmt = select(SalesOrder).options(*self._default_options()).join(SalesOrder.customer)

        if status is not None:
            stmt = stmt.where(SalesOrder.status == status)
        if customer_id is not None:
            stmt = stmt.where(SalesOrder.customer_id == customer_id)
        if sales_rep_id is not None:
            stmt = stmt.where(SalesOrder.sales_rep_id == sales_rep_id)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    SalesOrder.order_number.ilike(pattern),
                    Customer.name.ilike(pattern),
                    Customer.customer_code.ilike(pattern),
                )
            )

        stmt = stmt.order_by(SalesOrder.created_at.desc()).offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().unique().all())
