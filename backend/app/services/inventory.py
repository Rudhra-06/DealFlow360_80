from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory
from app.repositories.inventory import InventoryRepository
from app.repositories.product import ProductRepository
from app.repositories.warehouse import WarehouseRepository
from app.schemas.inventory import InventoryCreate, InventoryUpdate
from app.services.exceptions import (
    DuplicateResourceError,
    InactiveReferenceError,
    InvalidReferenceError,
    InventoryValidationError,
    ResourceNotFoundError,
)


class InventoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db
        self.inventory_repo: InventoryRepository = InventoryRepository()
        self.warehouse_repo: WarehouseRepository = WarehouseRepository()
        self.product_repo: ProductRepository = ProductRepository()

    async def get_inventory_by_id(self, inventory_id: int) -> Inventory:
        inv = await self.inventory_repo.get_by_id_with_relations(self.db, inventory_id)
        if not inv:
            raise ResourceNotFoundError(f"Inventory with ID {inventory_id} not found.")
        return inv

    async def list_inventory(
        self,
        warehouse_id: Optional[int] = None,
        product_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Inventory]:
        return await self.inventory_repo.list_inventory(
            self.db,
            warehouse_id=warehouse_id,
            product_id=product_id,
            limit=limit,
            offset=offset,
        )

    async def create_inventory(self, data: InventoryCreate) -> Inventory:
        # 1. Warehouse Validation
        wh = await self.warehouse_repo.get_by_id(self.db, data.warehouse_id)
        if not wh:
            raise InvalidReferenceError(f"Warehouse with ID {data.warehouse_id} does not exist.")
        if not wh.is_active:
            raise InactiveReferenceError(f"Cannot create inventory for inactive Warehouse '{wh.name}'.")

        # 2. Product Validation
        prod = await self.product_repo.get_by_id(self.db, data.product_id)
        if not prod:
            raise InvalidReferenceError(f"Product with ID {data.product_id} does not exist.")
        if not prod.is_active:
            raise InactiveReferenceError(f"Cannot create inventory for inactive Product '{prod.name}'.")

        # 3. Unique Mapping Validation
        existing = await self.inventory_repo.get_by_warehouse_and_product(
            self.db, data.warehouse_id, data.product_id
        )
        if existing:
            raise DuplicateResourceError(
                f"Inventory record for Warehouse ID {data.warehouse_id} and Product ID {data.product_id} already exists."
            )

        inv = Inventory(
            warehouse_id=data.warehouse_id,
            product_id=data.product_id,
            on_hand_qty=data.on_hand_qty,
            reserved_qty=Decimal("0.000"),
            reorder_level=data.reorder_level,
        )

        await self.inventory_repo.add(self.db, inv)

        try:
            await self.db.commit()
            return await self.get_inventory_by_id(inv.id)
        except Exception:
            await self.db.rollback()
            raise

    async def update_inventory(self, inventory_id: int, data: InventoryUpdate) -> Inventory:
        inv = await self.get_inventory_by_id(inventory_id)
        update_dict = data.model_dump(exclude_unset=True)

        if "on_hand_qty" in update_dict and update_dict["on_hand_qty"] is not None:
            new_on_hand: Decimal = update_dict["on_hand_qty"]
            if new_on_hand < inv.reserved_qty:
                raise InventoryValidationError(
                    f"Cannot set on_hand_qty ({new_on_hand}) below current reserved_qty ({inv.reserved_qty})."
                )
            inv.on_hand_qty = new_on_hand

        if "reorder_level" in update_dict and update_dict["reorder_level"] is not None:
            inv.reorder_level = update_dict["reorder_level"]

        try:
            await self.db.commit()
            return await self.get_inventory_by_id(inv.id)
        except Exception:
            await self.db.rollback()
            raise
