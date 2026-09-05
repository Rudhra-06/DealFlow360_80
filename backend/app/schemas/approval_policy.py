from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.customer_tier import CustomerTierRead


class ApprovalPolicyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable approval policy name")
    customer_tier_id: Optional[int] = Field(None, description="Optional target CustomerTier ID")
    discount_above_pct: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00"), description="Trigger approval if discount > %"
    )
    margin_below_pct: Optional[Decimal] = Field(
        None, ge=Decimal("-100.00"), le=Decimal("100.00"), description="Trigger approval if margin < %"
    )
    payment_terms_above_days: Optional[int] = Field(
        None, ge=0, description="Trigger approval if payment terms > N days"
    )
    blended_risk_above: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00"), description="Trigger approval if blended risk score > %"
    )
    approval_role: str = Field(..., description="Required operational approver role (SALES_MANAGER or FINANCE_OPERATIONS)")
    priority: int = Field(100, description="Priority ranking (lower integer = higher priority)")
    effective_from: Optional[datetime] = Field(None, description="Policy effective start timestamp")
    effective_to: Optional[datetime] = Field(None, description="Optional policy effective end timestamp")
    is_active: bool = Field(True, description="Administrative active flag")


class ApprovalPolicyCreate(ApprovalPolicyBase):
    pass


class ApprovalPolicyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    customer_tier_id: Optional[int] = None
    discount_above_pct: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("100.00"))
    margin_below_pct: Optional[Decimal] = Field(None, ge=Decimal("-100.00"), le=Decimal("100.00"))
    payment_terms_above_days: Optional[int] = Field(None, ge=0)
    blended_risk_above: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("100.00"))
    approval_role: Optional[str] = None
    priority: Optional[int] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    is_active: Optional[bool] = None


class ApprovalPolicyRead(ApprovalPolicyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    customer_tier: Optional[CustomerTierRead] = None

    model_config = ConfigDict(from_attributes=True)
