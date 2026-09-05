from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.deal_health_signal import DealHealthSignal
from app.models.deal_health_snapshot import DealHealthSnapshot
from app.repositories.base import BaseRepository


class DealHealthSnapshotRepository(BaseRepository[DealHealthSnapshot]):
    def __init__(self) -> None:
        super().__init__(DealHealthSnapshot)

    def _default_options(self):
        return [
            selectinload(DealHealthSnapshot.signals),
            selectinload(DealHealthSnapshot.quotation),
            selectinload(DealHealthSnapshot.sales_order),
        ]

    async def create_snapshot(self, db: AsyncSession, snapshot: DealHealthSnapshot) -> DealHealthSnapshot:
        db.add(snapshot)
        await db.flush()
        return snapshot

    async def get_latest_by_quotation(self, db: AsyncSession, quotation_id: int) -> Optional[DealHealthSnapshot]:
        stmt = (
            select(DealHealthSnapshot)
            .options(*self._default_options())
            .where(DealHealthSnapshot.quotation_id == quotation_id)
            .order_by(DealHealthSnapshot.calculated_at.desc(), DealHealthSnapshot.id.desc())
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def list_by_quotation(
        self, db: AsyncSession, quotation_id: int, limit: int = 50
    ) -> List[DealHealthSnapshot]:
        stmt = (
            select(DealHealthSnapshot)
            .options(*self._default_options())
            .where(DealHealthSnapshot.quotation_id == quotation_id)
            .order_by(DealHealthSnapshot.calculated_at.desc(), DealHealthSnapshot.id.desc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
