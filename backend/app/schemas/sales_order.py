from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.customer import CustomerRead
from app.schemas.user import UserRead


class SalesOrderLineRead(BaseModel):
    id: int
    sales_order_id: int
    source_quote_line_id: Optional[int] = None
    source_quote_version_line_id: Optional[int] = None
    product_id: Optional[int] = None
    billing_plan_id: Optional[int] = None
    product_sku_snapshot: str
    product_name_snapshot: str
    product_description_snapshot: Optional[str] = None
    quantity: Decimal
    unit_list_price: Decimal
    unit_cost: Decimal
    line_discount_pct: Decimal
    effective_discount_pct: Decimal
    gross_line_total: Decimal
    discount_amount: Decimal
    net_line_total: Decimal
    line_cost: Decimal
    margin_amount: Decimal
    margin_pct: Decimal
    billing_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SalesOrderListItem(BaseModel):
    id: int
    order_number: str
    quotation_id: int
    confirmed_quote_version_id: int
    customer_id: int
    sales_rep_id: int
    status: str
    currency: str
    net_total: Decimal
    customer_confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SalesOrderRead(SalesOrderListItem):
    payment_terms_days: int
    gross_subtotal: Decimal
    discount_amount: Decimal
    total_cost: Decimal
    margin_amount: Decimal
    margin_pct: Decimal
    customer: Optional[CustomerRead] = None
    sales_rep: Optional[UserRead] = None
    lines: List[SalesOrderLineRead] = []

    model_config = ConfigDict(from_attributes=True)
