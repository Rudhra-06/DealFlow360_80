from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quotation import Quotation
from app.models.quote_version import QuoteVersion
from app.models.quote_version_line import QuoteVersionLine
from app.repositories.base import BaseRepository


class QuoteVersionRepository(BaseRepository[QuoteVersion]):
    def __init__(self) -> None:
        super().__init__(QuoteVersion)

    def _default_options(self):
        return [
            selectinload(QuoteVersion.lines).selectinload(QuoteVersionLine.product),
            selectinload(QuoteVersion.lines).selectinload(QuoteVersionLine.billing_plan),
            selectinload(QuoteVersion.created_by_user),
        ]

    async def create_version(self, db: AsyncSession, version: QuoteVersion) -> QuoteVersion:
        db.add(version)
        await db.flush()
        return version

    async def get_by_id(self, db: AsyncSession, version_id: int) -> Optional[QuoteVersion]:
        stmt = select(QuoteVersion).options(*self._default_options()).where(QuoteVersion.id == version_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_number(self, db: AsyncSession, quotation_id: int, version_number: int) -> Optional[QuoteVersion]:
        stmt = (
            select(QuoteVersion)
            .options(*self._default_options())
            .where(QuoteVersion.quotation_id == quotation_id, QuoteVersion.version_number == version_number)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_latest_version(self, db: AsyncSession, quotation_id: int) -> Optional[QuoteVersion]:
        stmt = (
            select(QuoteVersion)
            .options(*self._default_options())
            .where(QuoteVersion.quotation_id == quotation_id)
            .order_by(QuoteVersion.version_number.desc())
            .limit(1)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_next_version_number_with_lock(self, db: AsyncSession, quotation_id: int) -> int:
        """Locks the parent Quotation row to guarantee concurrency-safe next version number assignment."""
        lock_stmt = select(Quotation.id).where(Quotation.id == quotation_id).with_for_update()
        await db.execute(lock_stmt)

        stmt = select(func.coalesce(func.max(QuoteVersion.version_number), 0)).where(QuoteVersion.quotation_id == quotation_id)
        res = await db.execute(stmt)
        max_ver = res.scalar_one()
        return max_ver + 1

    async def list_versions(self, db: AsyncSession, quotation_id: int) -> List[QuoteVersion]:
        stmt = (
            select(QuoteVersion)
            .options(*self._default_options())
            .where(QuoteVersion.quotation_id == quotation_id)
            .order_by(QuoteVersion.version_number.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
