from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_category import ProductCategory
from app.repositories.product_category import ProductCategoryRepository
from app.schemas.product_category import ProductCategoryCreate, ProductCategoryUpdate
from app.services.exceptions import DuplicateResourceError, ResourceNotFoundError


class ProductCategoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db
        self.repo: ProductCategoryRepository = ProductCategoryRepository()

    async def get_category_by_id(self, category_id: int) -> ProductCategory:
        cat = await self.repo.get_by_id(self.db, category_id)
        if not cat:
            raise ResourceNotFoundError(f"ProductCategory with ID {category_id} not found.")
        return cat

    async def list_categories(
        self, is_active: Optional[bool] = None, limit: int = 100, offset: int = 0
    ) -> List[ProductCategory]:
        return await self.repo.list_categories(
            self.db, is_active=is_active, limit=limit, offset=offset
        )

    async def create_category(self, data: ProductCategoryCreate) -> ProductCategory:
        name_clean = data.name.strip()
        existing = await self.repo.get_by_name(self.db, name_clean)
        if existing:
            raise DuplicateResourceError(f"ProductCategory with name '{name_clean}' already exists.")

        cat = ProductCategory(
            name=name_clean,
            description=data.description.strip() if data.description else None,
            is_active=data.is_active,
        )
        await self.repo.add(self.db, cat)

        try:
            await self.db.commit()
            await self.db.refresh(cat)
            return cat
        except Exception:
            await self.db.rollback()
            raise

    async def update_category(self, category_id: int, data: ProductCategoryUpdate) -> ProductCategory:
        cat = await self.get_category_by_id(category_id)
        update_dict = data.model_dump(exclude_unset=True)

        if "name" in update_dict and update_dict["name"] is not None:
            name_clean = update_dict["name"].strip()
            if name_clean != cat.name:
                existing = await self.repo.get_by_name(self.db, name_clean)
                if existing:
                    raise DuplicateResourceError(f"ProductCategory with name '{name_clean}' already exists.")
                cat.name = name_clean

        if "description" in update_dict:
            cat.description = update_dict["description"].strip() if update_dict["description"] else None
        if "is_active" in update_dict and update_dict["is_active"] is not None:
            cat.is_active = update_dict["is_active"]

        try:
            await self.db.commit()
            await self.db.refresh(cat)
            return cat
        except Exception:
            await self.db.rollback()
            raise
