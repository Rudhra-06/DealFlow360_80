"""Analytics Schemas for Phase 6 Part 2."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GranularityEnum(str, Enum):
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"


class CurrencyAmount(BaseModel):
    currency: str
    amount: Decimal


class TrendPoint(BaseModel):
    period: str
    value: Decimal


class ExecutiveOverviewResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    quotation_count: int
    confirmed_quote_count: int
    confirmation_rate: Optional[Decimal] = None
    open_quote_count: int
    at_risk_deal_count: int
    critical_deal_count: int
    order_count: int
    orders_in_fulfillment: int
    backordered_order_count: int
    invoice_count: int
    active_subscription_count: int
    confirmed_order_value: Dict[str, Decimal] = Field(default_factory=dict)
    invoiced_value: Dict[str, Decimal] = Field(default_factory=dict)
    payments_received: Dict[str, Decimal] = Field(default_factory=dict)
    outstanding_receivables: Dict[str, Decimal] = Field(default_factory=dict)
    monthly_recurring_revenue: Dict[str, Decimal] = Field(default_factory=dict)
    average_approval_time_hours: Optional[Decimal] = None
    average_negotiation_cycle_hours: Optional[Decimal] = None


class ExecutiveOverviewTrendItem(BaseModel):
    period: str
    quotes_created: int
    quotes_confirmed: int
    orders_created: int
    invoices_issued: int
    payments_received_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    at_risk_deals: int


class ExecutiveOverviewTrendResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    granularity: GranularityEnum
    trend: List[ExecutiveOverviewTrendItem]


class QuotationFunnelStageCount(BaseModel):
    status: str
    count: int
    percentage: Optional[Decimal] = None


class QuotationFunnelResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    total_quotes_created: int
    quotes_submitted: int
    quotes_approved: int
    quotes_sent: int
    quotes_confirmed: int
    quotes_rejected: int
    quotes_cancelled: int
    approval_rate: Optional[Decimal] = None
    confirmation_rate: Optional[Decimal] = None
    stage_breakdown: List[QuotationFunnelStageCount]


class SalesRepPerformanceItem(BaseModel):
    sales_rep_id: int
    rep_name: str
    quotes_created: int
    quotes_sent: int
    quotes_confirmed: int
    confirmation_rate: Optional[Decimal] = None
    total_confirmed_value_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    average_quote_value_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    average_discount_pct: Optional[Decimal] = None
    average_margin_pct: Optional[Decimal] = None
    at_risk_deals: int
    critical_deals: int
    average_approval_time_hours: Optional[Decimal] = None
    average_negotiation_time_hours: Optional[Decimal] = None
    open_alert_count: int


class SalesPerformanceResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    reps: List[SalesRepPerformanceItem]


class DiscountAnalyticsItem(BaseModel):
    group_key: str
    group_name: str
    quote_count: int
    average_discount_pct: Optional[Decimal] = None
    min_discount_pct: Optional[Decimal] = None
    max_discount_pct: Optional[Decimal] = None
    high_discount_quote_count: int
    discount_anomaly_count: int


class DiscountAnalyticsResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    overall_average_discount_pct: Optional[Decimal] = None
    by_sales_rep: List[DiscountAnalyticsItem]
    by_customer_tier: List[DiscountAnalyticsItem]
    by_product_category: List[DiscountAnalyticsItem]


class MarginAnalyticsItem(BaseModel):
    group_key: str
    group_name: str
    quote_count: int
    simple_average_margin_pct: Optional[Decimal] = None
    weighted_margin_pct: Optional[Decimal] = None
    negative_margin_deal_count: int


class MarginAnalyticsResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    overall_simple_average_margin_pct: Optional[Decimal] = None
    overall_weighted_margin_pct: Optional[Decimal] = None
    by_sales_rep: List[MarginAnalyticsItem]
    by_product_category: List[MarginAnalyticsItem]
    by_customer_tier: List[MarginAnalyticsItem]


# Customer 360
class Customer360Profile(BaseModel):
    customer_id: int
    customer_code: str
    name: str
    customer_tier: Optional[str] = None
    assigned_sales_rep: Optional[str] = None
    is_active: bool
    created_at: datetime


class Customer360Commercial(BaseModel):
    total_quotations: int
    open_quotations: int
    confirmed_quotations: int
    confirmation_rate: Optional[Decimal] = None
    latest_quote_number: Optional[str] = None
    average_discount_pct: Optional[Decimal] = None
    average_margin_pct: Optional[Decimal] = None
    confirmed_value_by_currency: Dict[str, Decimal] = Field(default_factory=dict)


class Customer360DealHealth(BaseModel):
    health_score: Optional[Decimal] = None
    health_level: Optional[str] = None
    open_alert_count: int
    top_signals: List[str] = Field(default_factory=list)
    last_activity_at: Optional[datetime] = None


class Customer360Orders(BaseModel):
    total_orders: int
    open_orders: int
    in_fulfillment_orders: int
    backordered_orders: int
    latest_order_number: Optional[str] = None
    recent_shipment_count: int


class Customer360Billing(BaseModel):
    invoice_count: int
    outstanding_invoices: int
    overdue_invoices: int
    invoiced_value_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    payments_received_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    outstanding_balance_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    credit_note_count: int


class Customer360Subscriptions(BaseModel):
    active_subscriptions: int
    monthly_recurring_revenue: Dict[str, Decimal] = Field(default_factory=dict)
    next_billing_date: Optional[datetime] = None


class Customer360ActivityItem(BaseModel):
    event_type: str
    title: str
    description: Optional[str] = None
    timestamp: datetime
    reference_id: Optional[str] = None


class Customer360Response(BaseModel):
    customer: Customer360Profile
    commercial: Customer360Commercial
    deal_health: Customer360DealHealth
    orders: Customer360Orders
    billing: Customer360Billing
    subscriptions: Customer360Subscriptions
    recent_activity: List[Customer360ActivityItem]


# Product & Category
class ProductPerformanceItem(BaseModel):
    product_id: int
    sku: str
    name: str
    category_name: str
    quoted_quantity: Decimal
    quoted_value_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    confirmed_quantity: Decimal
    confirmed_value_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    order_quantity: Decimal
    invoiced_value_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    average_discount_pct: Optional[Decimal] = None
    average_margin_pct: Optional[Decimal] = None


class ProductPerformanceResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    products: List[ProductPerformanceItem]


class ProductCategoryPerformanceItem(BaseModel):
    category_id: int
    category_name: str
    quote_count: int
    confirmed_quote_count: int
    confirmed_quantity: Decimal
    revenue_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    average_discount_pct: Optional[Decimal] = None
    average_margin_pct: Optional[Decimal] = None


class ProductCategoryPerformanceResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    categories: List[ProductCategoryPerformanceItem]


class RecommendationAnalyticsResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    recommendation_rule_count: int
    recommendations_added: int
    recommendations_dismissed: int
    acceptance_rate: Optional[Decimal] = None


# Approval & Negotiation
class ApprovalAnalyticsResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    total_approval_rounds: int
    manager_approvals_count: int
    finance_approvals_count: int
    approved_count: int
    rejected_count: int
    returned_count: int
    average_manager_turnaround_hours: Optional[Decimal] = None
    average_finance_turnaround_hours: Optional[Decimal] = None
    average_total_approval_cycle_hours: Optional[Decimal] = None
    approval_delay_alert_count: int
    reapproval_round_count: int


class NegotiationAnalyticsResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    quotes_entered_negotiation: int
    counteroffers_received: int
    counteroffers_accepted: int
    counteroffers_rejected: int
    acceptance_rate: Optional[Decimal] = None
    average_negotiation_duration_hours: Optional[Decimal] = None
    reapproval_trigger_rate: Optional[Decimal] = None
    average_versions_per_confirmed_quote: Optional[Decimal] = None


# Deal Health Analytics
class DealHealthAnalyticsResponse(BaseModel):
    healthy_count: int
    watch_count: int
    at_risk_count: int
    critical_count: int
    average_health_score: Optional[Decimal] = None
    open_alert_count: int
    alerts_by_severity: Dict[str, int] = Field(default_factory=dict)
    alerts_by_type: Dict[str, int] = Field(default_factory=dict)


class DealHealthTrendPoint(BaseModel):
    period: str
    average_score: Optional[Decimal] = None
    healthy_count: int
    watch_count: int
    at_risk_count: int
    critical_count: int
    alerts_created: int
    alerts_resolved: int


class DealHealthTrendResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    granularity: GranularityEnum
    trend: List[DealHealthTrendPoint]


# Operations
class FulfillmentAnalyticsResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    order_count: int
    fully_allocated_orders: int
    backordered_orders: int
    partial_fulfillment_orders: int
    average_warehouses_per_order: Optional[Decimal] = None
    average_shipments_per_order: Optional[Decimal] = None
    single_warehouse_fulfillment_rate: Optional[Decimal] = None
    multi_warehouse_split_rate: Optional[Decimal] = None
    backorder_rate: Optional[Decimal] = None
    open_backorder_quantity: Decimal
    resolved_backorder_count: int
    manual_override_count: int
    manual_override_rate: Optional[Decimal] = None


class WarehouseAnalyticsItem(BaseModel):
    warehouse_id: int
    code: str
    name: str
    orders_allocated: int
    order_lines_allocated: int
    reserved_quantity: Decimal
    fulfilled_quantity: Decimal
    shipment_count: int
    estimated_shipping_cost_by_currency: Dict[str, Decimal] = Field(default_factory=dict)


class WarehouseAnalyticsResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    warehouses: List[WarehouseAnalyticsItem]


class BackorderAnalyticsResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    open_count: int
    partially_resolved_count: int
    resolved_count: int
    open_quantity: Decimal
    average_resolution_time_hours: Optional[Decimal] = None


class ShipmentAnalyticsResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    planned_count: int
    ready_count: int
    shipped_count: int
    delivered_count: int
    cancelled_count: int
    average_time_created_to_shipped_hours: Optional[Decimal] = None


# Financial & Billing
class BillingAnalyticsResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    invoice_count: int
    paid_invoice_count: int
    partially_paid_count: int
    overdue_invoice_count: int
    credit_note_count: int
    active_subscription_count: int
    invoiced_value_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    credited_value_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    paid_value_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    outstanding_balance_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    overdue_balance_by_currency: Dict[str, Decimal] = Field(default_factory=dict)


class ReceivablesAgingBucket(BaseModel):
    bucket_name: str  # CURRENT, 1-30 DAYS, 31-60 DAYS, 61-90 DAYS, 90+ DAYS
    invoice_count: int
    balance_by_currency: Dict[str, Decimal] = Field(default_factory=dict)


class ReceivablesAnalyticsResponse(BaseModel):
    as_of: datetime
    buckets: List[ReceivablesAgingBucket]
    total_outstanding_by_currency: Dict[str, Decimal] = Field(default_factory=dict)


class PaymentAnalyticsResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    payment_count: int
    total_received_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    average_payment_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    payments_by_method: Dict[str, int] = Field(default_factory=dict)


class SubscriptionAnalyticsResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    active_subscriptions: int
    pending_cancellation_count: int
    cancelled_count: int
    ended_count: int
    new_subscriptions_in_period: int
    monthly_recurring_revenue: Dict[str, Decimal] = Field(default_factory=dict)
    annualized_recurring_revenue: Dict[str, Decimal] = Field(default_factory=dict)
