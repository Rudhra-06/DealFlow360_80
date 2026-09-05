"""Report Export Schemas for Phase 6 Part 2."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from app.models.report_export_audit import ExportStatus


class ReportExportFormat(str, Enum):
    PDF = "PDF"
    XLSX = "XLSX"


class ReportTypeEnum(str, Enum):
    EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"
    QUOTATION_FUNNEL = "QUOTATION_FUNNEL"
    SALES_PERFORMANCE = "SALES_PERFORMANCE"
    CUSTOMER_360 = "CUSTOMER_360"
    PRODUCT_PERFORMANCE = "PRODUCT_PERFORMANCE"
    APPROVAL_ANALYTICS = "APPROVAL_ANALYTICS"
    NEGOTIATION_ANALYTICS = "NEGOTIATION_ANALYTICS"
    DEAL_HEALTH = "DEAL_HEALTH"
    FULFILLMENT = "FULFILLMENT"
    BACKORDERS = "BACKORDERS"
    BILLING = "BILLING"
    RECEIVABLES = "RECEIVABLES"
    SUBSCRIPTIONS = "SUBSCRIPTIONS"


class ReportExportRequest(BaseModel):
    report_type: ReportTypeEnum
    format: ReportExportFormat
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    customer_id: Optional[int] = None
    sales_rep_id: Optional[int] = None
    currency: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class ReportExportAuditRead(BaseModel):
    id: int
    user_id: int
    report_type: str
    format: str
    filters_json: Optional[Dict[str, Any]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    generated_at: datetime
    row_count: Optional[int] = None
    status: ExportStatus
    filename: str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class ReportExportAuditListItem(BaseModel):
    id: int
    user_id: int
    report_type: str
    format: str
    generated_at: datetime
    status: ExportStatus
    filename: str

    class Config:
        from_attributes = True
