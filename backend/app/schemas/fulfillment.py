from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FulfillmentAllocationRead(BaseModel):
    id: int
    fulfillment_plan_id: int
    sales_order_line_id: int
    warehouse_id: int
    allocated_qty: Decimal
    reserved_qty: Decimal
    fulfilled_qty: Decimal
    estimated_shipping_cost: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FulfillmentPlanRead(BaseModel):
    id: int
    sales_order_id: int
    plan_version: int
    plan_type: str
    status: str
    estimated_shipment_count: int
    estimated_shipping_cost: Decimal
    created_by_user_id: Optional[int] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    allocations: List[FulfillmentAllocationRead] = []

    model_config = ConfigDict(from_attributes=True)


class BackorderRead(BaseModel):
    id: int
    sales_order_id: int
    sales_order_line_id: int
    requested_qty: Decimal
    backordered_qty: Decimal
    fulfilled_from_backorder_qty: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LineAllocationItem(BaseModel):
    sales_order_line_id: int
    product_id: int
    warehouse_id: int
    warehouse_code: str
    allocated_quantity: Decimal
    estimated_shipping_cost: Decimal


class FulfillmentPreviewRead(BaseModel):
    plan_type: str
    allocations: List[LineAllocationItem]
    backorders: List[Dict[str, Any]]
    estimated_shipment_count: int
    estimated_shipping_cost: Decimal
    explanation: str


class ManualAllocationInput(BaseModel):
    order_line_id: int
    warehouse_id: int
    quantity: Decimal = Field(..., gt=Decimal("0.0000"))


class ManualOverrideRequest(BaseModel):
    allocations: List[ManualAllocationInput]
