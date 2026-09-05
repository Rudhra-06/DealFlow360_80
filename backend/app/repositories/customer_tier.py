from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer_tier import CustomerTier
from app.repositories.base import BaseRepository


class CustomerTierRepository(BaseRepository[CustomerTier]):
    def __init__(self) -> None:
        super().__init__(CustomerTier)

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[CustomerTier]:
        result = await db.execute(
            select(CustomerTier).where(CustomerTier.name == name)
        )
        return result.scalar_one_or_none()

    async def list_tiers(
        self,
        db: AsyncSession,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CustomerTier]:
        stmt = select(CustomerTier)
        if is_active is not None:
            stmt = stmt.where(CustomerTier.is_active == is_active)
        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())
