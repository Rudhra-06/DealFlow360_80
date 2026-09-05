from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.warehouse import Warehouse
from app.repositories.base import BaseRepository


class WarehouseRepository(BaseRepository[Warehouse]):
    def __init__(self) -> None:
        super().__init__(Warehouse)

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[Warehouse]:
        result = await db.execute(
            select(Warehouse).where(Warehouse.code == code)
        )
        return result.scalar_one_or_none()

    async def list_warehouses(
        self,
        db: AsyncSession,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Warehouse]:
        stmt = select(Warehouse)
        if is_active is not None:
            stmt = stmt.where(Warehouse.is_active == is_active)
        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())
