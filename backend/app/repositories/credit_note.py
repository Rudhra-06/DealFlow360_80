from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.credit_note import CreditNote
from app.models.credit_note_line import CreditNoteLine
from app.models.customer import Customer
from app.repositories.base import BaseRepository


class CreditNoteRepository(BaseRepository[CreditNote]):
    def __init__(self) -> None:
        super().__init__(CreditNote)

    def _default_options(self):
        return [
            selectinload(CreditNote.customer).selectinload(Customer.tier),
            selectinload(CreditNote.sales_order),
            selectinload(CreditNote.lines),
        ]

    async def create_credit_note(self, db: AsyncSession, cn: CreditNote) -> CreditNote:
        db.add(cn)
        await db.flush()
        return cn

    async def get_by_id(self, db: AsyncSession, credit_note_id: int) -> Optional[CreditNote]:
        stmt = (
            select(CreditNote)
            .options(*self._default_options())
            .execution_options(populate_existing=True)
            .where(CreditNote.id == credit_note_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_number(self, db: AsyncSession, credit_note_number: str) -> Optional[CreditNote]:
        stmt = select(CreditNote).options(*self._default_options()).where(CreditNote.credit_note_number == credit_note_number)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_credit_notes(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        sales_order_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CreditNote]:
        stmt = select(CreditNote).options(*self._default_options())

        if status is not None:
            stmt = stmt.where(CreditNote.status == status)
        if customer_id is not None:
            stmt = stmt.where(CreditNote.customer_id == customer_id)
        if sales_order_id is not None:
            stmt = stmt.where(CreditNote.sales_order_id == sales_order_id)

        stmt = stmt.order_by(CreditNote.created_at.desc()).offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())
