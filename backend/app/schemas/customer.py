from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.customer_tier import CustomerTierRead


class CustomerBase(BaseModel):
    customer_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    tier_id: int
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    default_payment_terms_days: int = Field(30, ge=0)
    credit_limit: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    currency: str = Field("USD", min_length=3, max_length=3)


class CustomerCreate(CustomerBase):
    is_active: bool = True


class CustomerUpdate(BaseModel):
    customer_code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    tier_id: Optional[int] = None
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    default_payment_terms_days: Optional[int] = Field(None, ge=0)
    credit_limit: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    is_active: Optional[bool] = None


class CustomerRead(CustomerBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    tier: Optional[CustomerTierRead] = None

    model_config = ConfigDict(from_attributes=True)
