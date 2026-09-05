from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quote_approval_step import QuoteApprovalStep
from app.models.quote_approval_trigger import QuoteApprovalTrigger
from app.repositories.base import BaseRepository


class QuoteApprovalStepRepository(BaseRepository[QuoteApprovalStep]):
    def __init__(self) -> None:
        super().__init__(QuoteApprovalStep)

    def _default_options(self):
        return [
            selectinload(QuoteApprovalStep.decided_by_user),
            selectinload(QuoteApprovalStep.triggers),
        ]

    async def create_step(self, db: AsyncSession, step: QuoteApprovalStep) -> QuoteApprovalStep:
        db.add(step)
        await db.flush()
        return step

    async def get_by_id(self, db: AsyncSession, step_id: int) -> Optional[QuoteApprovalStep]:
        stmt = (
            select(QuoteApprovalStep)
            .options(*self._default_options())
            .where(QuoteApprovalStep.id == step_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_quotation(self, db: AsyncSession, quotation_id: int) -> List[QuoteApprovalStep]:
        stmt = (
            select(QuoteApprovalStep)
            .options(*self._default_options())
            .where(QuoteApprovalStep.quotation_id == quotation_id)
            .order_by(QuoteApprovalStep.approval_round.asc(), QuoteApprovalStep.sequence.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_round(self, db: AsyncSession, quotation_id: int) -> int:
        stmt = (
            select(QuoteApprovalStep.approval_round)
            .where(QuoteApprovalStep.quotation_id == quotation_id)
            .order_by(QuoteApprovalStep.approval_round.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        val = result.scalar_one_or_none()
        return val if val is not None else 0
