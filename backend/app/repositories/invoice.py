from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.invoice_line import InvoiceLine
from app.models.sales_order import SalesOrder
from app.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self) -> None:
        super().__init__(Invoice)

    def _default_options(self):
        return [
            selectinload(Invoice.customer).selectinload(Customer.tier),
            selectinload(Invoice.sales_order),
            selectinload(Invoice.lines),
        ]

    async def create_invoice(self, db: AsyncSession, invoice: Invoice) -> Invoice:
        db.add(invoice)
        await db.flush()
        return invoice

    async def get_by_id(self, db: AsyncSession, invoice_id: int) -> Optional[Invoice]:
        stmt = (
            select(Invoice)
            .options(*self._default_options())
            .execution_options(populate_existing=True)
            .where(Invoice.id == invoice_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_number(self, db: AsyncSession, invoice_number: str) -> Optional[Invoice]:
        stmt = select(Invoice).options(*self._default_options()).where(Invoice.invoice_number == invoice_number)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_order(self, db: AsyncSession, sales_order_id: int) -> List[Invoice]:
        stmt = (
            select(Invoice)
            .options(*self._default_options())
            .where(Invoice.sales_order_id == sales_order_id)
            .order_by(Invoice.created_at.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def list_invoices(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        sales_order_id: Optional[int] = None,
        invoice_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Invoice]:
        stmt = select(Invoice).options(*self._default_options())

        if status is not None:
            stmt = stmt.where(Invoice.status == status)
        if customer_id is not None:
            stmt = stmt.where(Invoice.customer_id == customer_id)
        if sales_order_id is not None:
            stmt = stmt.where(Invoice.sales_order_id == sales_order_id)
        if invoice_type is not None:
            stmt = stmt.where(Invoice.invoice_type == invoice_type)

        stmt = stmt.order_by(Invoice.created_at.desc()).offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())
