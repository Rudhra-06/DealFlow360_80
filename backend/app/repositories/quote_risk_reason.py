from typing import List
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quote_risk_reason import QuoteRiskReason
from app.repositories.base import BaseRepository


class QuoteRiskReasonRepository(BaseRepository[QuoteRiskReason]):
    def __init__(self) -> None:
        super().__init__(QuoteRiskReason)

    async def replace_reasons_for_quotation(
        self, db: AsyncSession, quotation_id: int, reasons: List[QuoteRiskReason]
    ) -> List[QuoteRiskReason]:
        # Transactionally remove current active risk reasons for quotation
        await db.execute(
            delete(QuoteRiskReason).where(QuoteRiskReason.quotation_id == quotation_id)
        )
        for r in reasons:
            r.quotation_id = quotation_id
            db.add(r)
        await db.flush()
        return reasons

    async def list_by_quotation(
        self, db: AsyncSession, quotation_id: int
    ) -> List[QuoteRiskReason]:
        stmt = (
            select(QuoteRiskReason)
            .where(QuoteRiskReason.quotation_id == quotation_id)
            .order_by(QuoteRiskReason.id.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
