from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.product import ProductRead
from app.schemas.warehouse import WarehouseRead


class InventoryCreate(BaseModel):
    warehouse_id: int
    product_id: int
    on_hand_qty: Decimal = Field(Decimal("0.000"), ge=Decimal("0.000"))
    reorder_level: Decimal = Field(Decimal("0.000"), ge=Decimal("0.000"))


class InventoryUpdate(BaseModel):
    on_hand_qty: Optional[Decimal] = Field(None, ge=Decimal("0.000"))
    reorder_level: Optional[Decimal] = Field(None, ge=Decimal("0.000"))


class InventoryRead(BaseModel):
    id: int
    warehouse_id: int
    product_id: int
    on_hand_qty: Decimal
    reserved_qty: Decimal
    reorder_level: Decimal
    created_at: datetime
    updated_at: datetime

    warehouse: Optional[WarehouseRead] = None
    product: Optional[ProductRead] = None

    @computed_field
    @property
    def available_qty(self) -> Decimal:
        return self.on_hand_qty - self.reserved_qty

    model_config = ConfigDict(from_attributes=True)
