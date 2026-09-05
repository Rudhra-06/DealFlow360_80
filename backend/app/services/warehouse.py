from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.warehouse import Warehouse
from app.repositories.warehouse import WarehouseRepository
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate
from app.services.exceptions import DuplicateResourceError, ResourceNotFoundError


class WarehouseService:
    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db
        self.repo: WarehouseRepository = WarehouseRepository()

    async def get_warehouse_by_id(self, warehouse_id: int) -> Warehouse:
        wh = await self.repo.get_by_id(self.db, warehouse_id)
        if not wh:
            raise ResourceNotFoundError(f"Warehouse with ID {warehouse_id} not found.")
        return wh

    async def list_warehouses(
        self, is_active: Optional[bool] = None, limit: int = 100, offset: int = 0
    ) -> List[Warehouse]:
        return await self.repo.list_warehouses(
            self.db, is_active=is_active, limit=limit, offset=offset
        )

    async def create_warehouse(self, data: WarehouseCreate) -> Warehouse:
        code_clean = data.code.strip().upper()
        existing = await self.repo.get_by_code(self.db, code_clean)
        if existing:
            raise DuplicateResourceError(f"Warehouse with code '{code_clean}' already exists.")

        wh = Warehouse(
            code=code_clean,
            name=data.name.strip(),
            location=data.location.strip() if data.location else None,
            address=data.address.strip() if data.address else None,
            is_active=data.is_active,
        )
        await self.repo.add(self.db, wh)

        try:
            await self.db.commit()
            await self.db.refresh(wh)
            return wh
        except Exception:
            await self.db.rollback()
            raise

    async def update_warehouse(self, warehouse_id: int, data: WarehouseUpdate) -> Warehouse:
        wh = await self.get_warehouse_by_id(warehouse_id)
        update_dict = data.model_dump(exclude_unset=True)

        if "code" in update_dict and update_dict["code"] is not None:
            code_clean = update_dict["code"].strip().upper()
            if code_clean != wh.code:
                existing = await self.repo.get_by_code(self.db, code_clean)
                if existing:
                    raise DuplicateResourceError(f"Warehouse with code '{code_clean}' already exists.")
                wh.code = code_clean

        if "name" in update_dict and update_dict["name"] is not None:
            wh.name = update_dict["name"].strip()
        if "location" in update_dict:
            wh.location = update_dict["location"].strip() if update_dict["location"] else None
        if "address" in update_dict:
            wh.address = update_dict["address"].strip() if update_dict["address"] else None
        if "is_active" in update_dict and update_dict["is_active"] is not None:
            wh.is_active = update_dict["is_active"]

        try:
            await self.db.commit()
            await self.db.refresh(wh)
            return wh
        except Exception:
            await self.db.rollback()
            raise
