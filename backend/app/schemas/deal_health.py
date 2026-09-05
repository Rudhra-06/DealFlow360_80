from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# --- CONFIG SCHEMAS ---

class DealHealthConfigBase(BaseModel):
    name: str = Field(default="Default Health Policy", max_length=100)
    is_active: bool = True

    healthy_min_score: Decimal = Field(default=Decimal("80.00"), ge=Decimal("0.00"), le=Decimal("100.00"))
    watch_min_score: Decimal = Field(default=Decimal("60.00"), ge=Decimal("0.00"), le=Decimal("100.00"))
    at_risk_min_score: Decimal = Field(default=Decimal("30.00"), ge=Decimal("0.00"), le=Decimal("100.00"))

    stalled_quote_days: int = Field(default=5, ge=0)
    approval_delay_hours: int = Field(default=24, ge=0)
    negotiation_stall_days: int = Field(default=3, ge=0)
    discount_anomaly_threshold_pct: Decimal = Field(default=Decimal("10.00"), ge=Decimal("0.00"))
    delivery_slippage_days: int = Field(default=2, ge=0)
    backorder_age_days: int = Field(default=3, ge=0)
    invoice_overdue_days: int = Field(default=1, ge=0)

    weight_stalled_quote: Decimal = Field(default=Decimal("20.00"), ge=Decimal("0.00"))
    weight_discount_anomaly: Decimal = Field(default=Decimal("15.00"), ge=Decimal("0.00"))
    weight_approval_delay: Decimal = Field(default=Decimal("10.00"), ge=Decimal("0.00"))
    weight_negotiation_stall: Decimal = Field(default=Decimal("15.00"), ge=Decimal("0.00"))
    weight_delivery_slippage: Decimal = Field(default=Decimal("20.00"), ge=Decimal("0.00"))
    weight_backorder: Decimal = Field(default=Decimal("10.00"), ge=Decimal("0.00"))
    weight_invoice_overdue: Decimal = Field(default=Decimal("10.00"), ge=Decimal("0.00"))


class DealHealthConfigCreate(DealHealthConfigBase):
    pass


class DealHealthConfigUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None

    healthy_min_score: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"), le=Decimal("100.00"))
    watch_min_score: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"), le=Decimal("100.00"))
    at_risk_min_score: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"), le=Decimal("100.00"))

    stalled_quote_days: Optional[int] = Field(default=None, ge=0)
    approval_delay_hours: Optional[int] = Field(default=None, ge=0)
    negotiation_stall_days: Optional[int] = Field(default=None, ge=0)
    discount_anomaly_threshold_pct: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    delivery_slippage_days: Optional[int] = Field(default=None, ge=0)
    backorder_age_days: Optional[int] = Field(default=None, ge=0)
    invoice_overdue_days: Optional[int] = Field(default=None, ge=0)

    weight_stalled_quote: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    weight_discount_anomaly: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    weight_approval_delay: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    weight_negotiation_stall: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    weight_delivery_slippage: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    weight_backorder: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    weight_invoice_overdue: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))


class DealHealthConfigRead(DealHealthConfigBase):
    id: int
    created_by_user_id: Optional[int] = None
    updated_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- SIGNAL & SNAPSHOT SCHEMAS ---

class DealHealthSignalRead(BaseModel):
    id: int
    snapshot_id: int
    signal_type: str
    severity: str
    score_penalty: Decimal
    title: str
    explanation: str
    metric_value: Optional[Decimal] = None
    threshold_value: Optional[Decimal] = None
    signal_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DealHealthSnapshotRead(BaseModel):
    id: int
    quotation_id: int
    sales_order_id: Optional[int] = None
    config_id: Optional[int] = None
    health_score: Decimal
    health_level: str
    signal_count: int
    summary: str
    calculated_at: datetime
    created_at: datetime
    signals: List[DealHealthSignalRead] = []

    model_config = ConfigDict(from_attributes=True)


class DealHealthHistoryItem(BaseModel):
    id: int
    quotation_id: int
    health_score: Decimal
    health_level: str
    signal_count: int
    summary: str
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DealHealthListItem(BaseModel):
    quotation_id: int
    quote_number: str
    customer_id: int
    customer_name: str
    sales_rep_id: int
    sales_rep_name: str
    quotation_status: str
    health_score: Decimal
    health_level: str
    top_signal_title: Optional[str] = None
    open_alert_count: int = 0
    last_activity_at: Optional[datetime] = None
    calculated_at: datetime


# --- ALERT & ACTION SCHEMAS ---

class DealActionRead(BaseModel):
    id: int
    deal_alert_id: int
    quotation_id: int
    action_type: str
    status: str
    target_user_id: Optional[int] = None
    created_by_user_id: int
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DealAlertRead(BaseModel):
    id: int
    quotation_id: int
    sales_order_id: Optional[int] = None
    snapshot_id: Optional[int] = None
    alert_type: str
    severity: str
    status: str
    title: str
    message: str
    assigned_user_id: Optional[int] = None
    created_at: datetime
    last_triggered_at: Optional[datetime] = None
    occurrence_count: int
    acknowledged_at: Optional[datetime] = None
    acknowledged_by_user_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolved_by_user_id: Optional[int] = None
    resolution_note: Optional[str] = None
    actions: List[DealActionRead] = []

    model_config = ConfigDict(from_attributes=True)


class DealAlertListItem(BaseModel):
    id: int
    quotation_id: int
    quote_number: str
    customer_name: str
    sales_rep_name: str
    alert_type: str
    severity: str
    status: str
    title: str
    message: str
    created_at: datetime
    last_triggered_at: Optional[datetime] = None
    occurrence_count: int


class DealAlertResolveRequest(BaseModel):
    resolution_note: str = Field(..., min_length=3, max_length=1000)


class DealAlertDismissRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=1000)


class DealNudgeRequest(BaseModel):
    action_type: str = Field(default="NUDGE_SALES_REP")
    message: Optional[str] = None


class DealEscalateRequest(BaseModel):
    message: Optional[str] = None


# --- BULK SCAN SCHEMAS ---

class DealHealthScanRequest(BaseModel):
    as_of: Optional[datetime] = None


class DealHealthScanResult(BaseModel):
    evaluated_count: int
    healthy_count: int
    watch_count: int
    at_risk_count: int
    critical_count: int
    alerts_created: int
    alerts_updated: int
