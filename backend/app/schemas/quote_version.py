from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class QuoteVersionLineRead(BaseModel):
    id: int
    quote_version_id: int
    original_quote_line_id: Optional[int] = None
    product_id: Optional[int] = None
    billing_plan_id: Optional[int] = None

    product_sku_snapshot: str
    product_name_snapshot: str

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

    standard_discount_pct_snapshot: Optional[Decimal] = None
    max_discount_pct_snapshot: Optional[Decimal] = None

    risk_level: str
    source_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuoteVersionRead(BaseModel):
    id: int
    quotation_id: int
    version_number: int
    source_type: str
    created_by_user_id: Optional[int] = None
    status_snapshot: str
    approval_status: str
    currency: str
    payment_terms_days: int
    order_discount_pct: Decimal

    gross_subtotal: Decimal
    discount_amount: Decimal
    net_total: Decimal
    total_cost: Decimal
    margin_amount: Decimal
    margin_pct: Decimal
    weighted_effective_discount_pct: Decimal

    blended_risk_score: Decimal
    risk_level: str
    source_negotiation_request_id: Optional[int] = None
    created_at: datetime

    lines: List[QuoteVersionLineRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class VersionDiffChange(BaseModel):
    field_name: str
    from_value: Any
    to_value: Any


class VersionLineDiff(BaseModel):
    product_sku: str
    product_name: str
    change_type: str  # "ADDED", "REMOVED", "MODIFIED"
    changes: List[VersionDiffChange] = Field(default_factory=list)


class QuoteVersionCompareResult(BaseModel):
    from_version: int
    to_version: int
    quote_changes: List[VersionDiffChange] = Field(default_factory=list)
    lines_added: List[Dict[str, Any]] = Field(default_factory=list)
    lines_removed: List[Dict[str, Any]] = Field(default_factory=list)
    lines_changed: List[VersionLineDiff] = Field(default_factory=list)

    @property
    def from_version_number(self) -> int:
        return self.from_version

    @property
    def to_version_number(self) -> int:
        return self.to_version

    @property
    def header_changes(self) -> Dict[str, Dict[str, Any]]:
        labels_to_attrs = {
            "Payment Terms (Days)": "payment_terms_days",
            "Order Discount %": "order_discount_pct",
            "Gross Subtotal": "gross_subtotal",
            "Discount Amount": "discount_amount",
            "Net Total": "net_total",
            "Total Cost": "total_cost",
            "Margin Amount": "margin_amount",
            "Margin %": "margin_pct",
            "Blended Risk Score": "blended_risk_score",
            "Risk Level": "risk_level",
        }
        res: Dict[str, Dict[str, Any]] = {}
        for c in self.quote_changes:
            res[c.field_name] = {"from": c.from_value, "to": c.to_value}
            attr_key = labels_to_attrs.get(c.field_name)
            if attr_key:
                res[attr_key] = {"from": c.from_value, "to": c.to_value}
        return res

    @property
    def added_lines(self) -> List[Dict[str, Any]]:
        return self.lines_added

    @property
    def removed_lines(self) -> List[Dict[str, Any]]:
        return self.lines_removed
