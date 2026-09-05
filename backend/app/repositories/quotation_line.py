from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quotation_line import QuoteLine
from app.repositories.base import BaseRepository


class QuoteLineRepository(BaseRepository[QuoteLine]):
    def __init__(self) -> None:
        super().__init__(QuoteLine)

    def _default_options(self):
        return [
            selectinload(QuoteLine.product),
            selectinload(QuoteLine.billing_plan),
            selectinload(QuoteLine.resolved_discount_policy),
        ]

    async def create_line(self, db: AsyncSession, line: QuoteLine) -> QuoteLine:
        db.add(line)
        await db.flush()
        return line

    async def get_by_id(self, db: AsyncSession, line_id: int) -> Optional[QuoteLine]:
        stmt = (
            select(QuoteLine)
            .options(*self._default_options())
            .where(QuoteLine.id == line_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_quotation(self, db: AsyncSession, quotation_id: int) -> List[QuoteLine]:
        stmt = (
            select(QuoteLine)
            .options(*self._default_options())
            .where(QuoteLine.quotation_id == quotation_id)
            .order_by(QuoteLine.id.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def delete_line(self, db: AsyncSession, line: QuoteLine) -> None:
        await db.delete(line)
        await db.flush()
