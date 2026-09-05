from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class InvoiceLineRead(BaseModel):
    id: int
    invoice_id: int
    sales_order_line_id: Optional[int] = None
    subscription_id: Optional[int] = None
    line_type: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    billing_period_start: Optional[datetime] = None
    billing_period_end: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceRead(BaseModel):
    id: int
    invoice_number: str
    sales_order_id: Optional[int] = None
    customer_id: int
    invoice_type: str
    status: str
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    credited_amount: Decimal
    paid_amount: Decimal
    balance_due: Decimal
    issue_date: datetime
    due_date: datetime
    billing_period_start: Optional[datetime] = None
    billing_period_end: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    paid_at: Optional[datetime] = None
    lines: List[InvoiceLineRead] = []

    model_config = ConfigDict(from_attributes=True)
