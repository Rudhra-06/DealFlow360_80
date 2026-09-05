from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.billing_plan import BillingPlanRead
from app.schemas.discount_policy import DiscountPolicyRead
from app.schemas.product import ProductRead


class QuoteLineCreate(BaseModel):
    product_id: int = Field(..., description="ID of Product to add")
    quantity: Decimal = Field(..., gt=Decimal("0.000"), description="Quantity must be greater than 0")
    line_discount_pct: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00"), description="Optional line-level discount %"
    )
    billing_plan_id: Optional[int] = Field(None, description="Optional associated BillingPlan ID")


class QuoteLineUpdate(BaseModel):
    quantity: Optional[Decimal] = Field(None, gt=Decimal("0.000"), description="Updated line quantity")
    line_discount_pct: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00"), description="Updated line discount %"
    )
    billing_plan_id: Optional[int] = Field(None, description="Updated BillingPlan ID")


class QuoteLineRead(BaseModel):
    id: int
    quotation_id: int
    product_id: int
    billing_plan_id: Optional[int] = None
    quantity: Decimal

    # Historical Snapshots
    unit_list_price: Decimal
    unit_cost: Decimal

    line_discount_pct: Decimal
    effective_discount_pct: Decimal

    # Calculated Financial Totals
    gross_line_total: Decimal
    discount_amount: Decimal
    net_line_total: Decimal
    line_cost: Decimal
    margin_amount: Decimal
    margin_pct: Decimal

    # Policy Context & Risk
    resolved_discount_policy_id: Optional[int] = None
    standard_discount_pct_snapshot: Optional[Decimal] = None
    max_discount_pct_snapshot: Optional[Decimal] = None
    discount_overage_pct: Decimal
    risk_level: str
    source_type: str

    created_at: datetime
    updated_at: datetime

    product: Optional[ProductRead] = None
    billing_plan: Optional[BillingPlanRead] = None
    resolved_discount_policy: Optional[DiscountPolicyRead] = None

    model_config = ConfigDict(from_attributes=True)
