from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deal_health_config import DealHealthConfig
from app.repositories.base import BaseRepository


class DealHealthConfigRepository(BaseRepository[DealHealthConfig]):
    def __init__(self) -> None:
        super().__init__(DealHealthConfig)

    async def get_active_config(self, db: AsyncSession) -> Optional[DealHealthConfig]:
        stmt = (
            select(DealHealthConfig)
            .where(DealHealthConfig.is_active == True)
            .order_by(DealHealthConfig.updated_at.desc(), DealHealthConfig.id.desc())
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def deactivate_all_configs(self, db: AsyncSession) -> None:
        stmt = update(DealHealthConfig).where(DealHealthConfig.is_active == True).values(is_active=False)
        await db.execute(stmt)

    async def create_config(self, db: AsyncSession, config: DealHealthConfig) -> DealHealthConfig:
        db.add(config)
        await db.flush()
        return config
