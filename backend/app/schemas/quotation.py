from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.customer import CustomerRead
from app.schemas.quote_risk_reason import QuoteRiskReasonRead
from app.schemas.quotation_line import QuoteLineRead
from app.schemas.user import UserRead


class QuotationCreate(BaseModel):
    customer_id: int = Field(..., description="ID of target Customer")
    payment_terms_days: Optional[int] = Field(30, ge=0, description="Payment terms due days (>= 0)")
    order_discount_pct: Optional[Decimal] = Field(
        Decimal("0.00"), ge=Decimal("0.00"), le=Decimal("100.00"), description="Order-level discount %"
    )


class QuotationUpdate(BaseModel):
    payment_terms_days: Optional[int] = Field(None, ge=0, description="Updated payment terms in days")
    order_discount_pct: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00"), description="Updated order-level discount %"
    )


class QuotationListItem(BaseModel):
    id: int
    quote_number: str
    customer_id: Optional[int] = None
    sales_rep_id: Optional[int] = None
    status: str
    currency: str
    payment_terms_days: int = 30
    order_discount_pct: Decimal = Decimal("0.00")
    gross_subtotal: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    net_total: Decimal = Decimal("0.00")
    margin_pct: Optional[Decimal] = Decimal("0.00")
    weighted_effective_discount_pct: Optional[Decimal] = Decimal("0.00")
    blended_risk_score: Optional[Decimal] = Decimal("0.00")
    risk_level: Optional[str] = "GREEN"
    created_at: datetime
    updated_at: datetime
    customer: Optional[CustomerRead] = None
    sales_rep: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)


class QuotationRead(BaseModel):
    id: int
    quote_number: str
    customer_id: Optional[int] = None
    sales_rep_id: Optional[int] = None
    status: str
    currency: str
    payment_terms_days: int = 30
    order_discount_pct: Decimal = Decimal("0.00")

    gross_subtotal: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    net_total: Decimal = Decimal("0.00")
    total_cost: Optional[Decimal] = Decimal("0.00")
    margin_amount: Optional[Decimal] = Decimal("0.00")
    margin_pct: Optional[Decimal] = Decimal("0.00")
    weighted_effective_discount_pct: Optional[Decimal] = Decimal("0.00")

    blended_risk_score: Optional[Decimal] = Decimal("0.00")
    risk_level: Optional[str] = "GREEN"

    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    customer: Optional[CustomerRead] = None
    sales_rep: Optional[UserRead] = None
    lines: List[QuoteLineRead] = []
    risk_reasons: List[QuoteRiskReasonRead] = []

    model_config = ConfigDict(from_attributes=True)


class QuoteRecalculationRead(BaseModel):
    quotation: QuotationRead
    message: str = "Quotation recalculated successfully."
