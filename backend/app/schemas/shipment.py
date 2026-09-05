from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.warehouse import WarehouseRead


class ShipmentLineRead(BaseModel):
    id: int
    shipment_id: int
    sales_order_line_id: int
    fulfillment_allocation_id: int
    quantity: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShipmentRead(BaseModel):
    id: int
    shipment_number: str
    sales_order_id: int
    warehouse_id: int
    status: str
    estimated_cost: Decimal
    actual_cost: Optional[Decimal] = None
    created_at: datetime
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    warehouse: Optional[WarehouseRead] = None
    lines: List[ShipmentLineRead] = []

    model_config = ConfigDict(from_attributes=True)
