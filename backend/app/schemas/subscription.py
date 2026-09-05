from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BillingScheduleRead(BaseModel):
    id: int
    subscription_id: int
    invoice_id: Optional[int] = None
    sequence: int
    period_start: datetime
    period_end: datetime
    billing_date: datetime
    scheduled_amount: Decimal
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriptionRead(BaseModel):
    id: int
    subscription_number: str
    sales_order_id: Optional[int] = None
    sales_order_line_id: Optional[int] = None
    customer_id: int
    billing_plan_id: Optional[int] = None
    status: str
    quantity: Decimal
    unit_price: Decimal
    monthly_recurring_revenue: Optional[Decimal] = None
    currency: str
    interval_months: int
    proration_method: str
    cancellation_method: str
    start_date: datetime
    current_period_start: datetime
    current_period_end: datetime
    next_billing_date: datetime
    cancel_at_period_end: bool
    cancelled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    schedules: List[BillingScheduleRead] = []

    model_config = ConfigDict(from_attributes=True)


class SubscriptionQuantityChangeRequest(BaseModel):
    new_quantity: float = Field(..., gt=0.0)
    effective_date: Optional[datetime] = None
    reason: Optional[str] = None


class SubscriptionCancelRequest(BaseModel):
    effective_date: Optional[datetime] = None
    reason: Optional[str] = None
