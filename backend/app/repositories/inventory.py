from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.inventory import Inventory
from app.models.product import Product
from app.repositories.base import BaseRepository


class InventoryRepository(BaseRepository[Inventory]):
    def __init__(self) -> None:
        super().__init__(Inventory)

    async def get_by_warehouse_and_product(
        self, db: AsyncSession, warehouse_id: int, product_id: int
    ) -> Optional[Inventory]:
        result = await db.execute(
            select(Inventory)
            .options(
                selectinload(Inventory.warehouse),
                selectinload(Inventory.product).selectinload(Product.category),
            )
            .where(
                Inventory.warehouse_id == warehouse_id,
                Inventory.product_id == product_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_relations(
        self, db: AsyncSession, inventory_id: int
    ) -> Optional[Inventory]:
        result = await db.execute(
            select(Inventory)
            .options(
                selectinload(Inventory.warehouse),
                selectinload(Inventory.product).selectinload(Product.category),
            )
            .where(Inventory.id == inventory_id)
        )
        return result.scalar_one_or_none()

    async def list_inventory(
        self,
        db: AsyncSession,
        warehouse_id: Optional[int] = None,
        product_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Inventory]:
        stmt = select(Inventory).options(
            selectinload(Inventory.warehouse),
            selectinload(Inventory.product).selectinload(Product.category),
        )

        if warehouse_id is not None:
            stmt = stmt.where(Inventory.warehouse_id == warehouse_id)
        if product_id is not None:
            stmt = stmt.where(Inventory.product_id == product_id)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())
