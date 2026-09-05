from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BillingPlanBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Unique billing plan code (e.g., MONTHLY, ONE_TIME)")
    name: str = Field(..., min_length=1, max_length=255, description="Display name for billing plan")
    billing_type: str = Field(..., description="Billing type ('ONE_TIME' or 'RECURRING')")
    billing_interval_months: Optional[int] = Field(None, ge=1, description="Interval in months for RECURRING plans")
    payment_due_days: int = Field(30, ge=0, description="Default payment terms due days for plan")
    description: Optional[str] = Field(None, description="Detailed billing plan description")
    is_active: bool = Field(True, description="Administrative active status")


class BillingPlanCreate(BillingPlanBase):
    pass


class BillingPlanUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    billing_type: Optional[str] = None
    billing_interval_months: Optional[int] = Field(None, ge=1)
    payment_due_days: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class BillingPlanRead(BillingPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
