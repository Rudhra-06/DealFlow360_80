from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PortalQuotationLineRead(BaseModel):
    id: int
    product_id: int
    product_sku: str
    product_name: str
    quantity: Decimal
    unit_list_price: Decimal
    line_discount_pct: Decimal
    effective_discount_pct: Decimal
    gross_line_total: Decimal
    discount_amount: Decimal
    net_line_total: Decimal
    billing_plan_name: Optional[str] = None


class PortalQuotationListItem(BaseModel):
    id: int
    quote_number: str
    status: str
    currency: str
    net_total: Decimal
    current_version_number: int = 1
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PortalQuotationRead(BaseModel):
    id: int
    quote_number: str
    status: str
    currency: str
    payment_terms_days: int
    order_discount_pct: Decimal

    gross_subtotal: Decimal
    discount_amount: Decimal
    net_total: Decimal

    current_version_number: int = 1
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    lines: List[PortalQuotationLineRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PortalQuoteVersionLineRead(BaseModel):
    id: int
    quote_version_id: int
    product_id: Optional[int] = None
    product_sku_snapshot: str
    product_name_snapshot: str
    quantity: Decimal
    unit_list_price: Decimal
    line_discount_pct: Decimal
    effective_discount_pct: Decimal
    gross_line_total: Decimal
    discount_amount: Decimal
    net_line_total: Decimal


class PortalQuoteVersionRead(BaseModel):
    id: int
    quotation_id: int
    version_number: int
    source_type: str
    status_snapshot: str
    approval_status: str
    currency: str
    payment_terms_days: int
    order_discount_pct: Decimal

    gross_subtotal: Decimal
    discount_amount: Decimal
    net_total: Decimal

    created_at: datetime
    lines: List[PortalQuoteVersionLineRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Customer-safe quotation detail schema alias
PortalQuotationDetail = PortalQuotationRead


class PortalInvoiceLineRead(BaseModel):
    id: int
    invoice_id: int
    line_type: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    billing_period_start: Optional[datetime] = None
    billing_period_end: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PortalInvoiceListItem(BaseModel):
    id: int
    invoice_number: str
    sales_order_id: Optional[int] = None
    invoice_type: str
    status: str
    currency: str
    total_amount: Decimal
    paid_amount: Decimal
    balance_due: Decimal
    issue_date: datetime
    due_date: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PortalInvoiceRead(BaseModel):
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
    paid_at: Optional[datetime] = None
    lines: List[PortalInvoiceLineRead] = []

    model_config = ConfigDict(from_attributes=True)


