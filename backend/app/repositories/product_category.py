from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_category import ProductCategory
from app.repositories.base import BaseRepository


class ProductCategoryRepository(BaseRepository[ProductCategory]):
    def __init__(self) -> None:
        super().__init__(ProductCategory)

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[ProductCategory]:
        result = await db.execute(
            select(ProductCategory).where(ProductCategory.name == name)
        )
        return result.scalar_one_or_none()

    async def list_categories(
        self,
        db: AsyncSession,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ProductCategory]:
        stmt = select(ProductCategory)
        if is_active is not None:
            stmt = stmt.where(ProductCategory.is_active == is_active)
        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())
