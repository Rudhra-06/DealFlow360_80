from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.customer_tier import CustomerTierRead
from app.schemas.product import ProductRead
from app.schemas.product_category import ProductCategoryRead


class DiscountPolicyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable policy name")
    customer_tier_id: Optional[int] = Field(None, description="Optional target CustomerTier ID")
    product_category_id: Optional[int] = Field(None, description="Optional target ProductCategory ID")
    product_id: Optional[int] = Field(None, description="Optional target Product ID")
    standard_discount_pct: Decimal = Field(
        Decimal("0.00"), ge=Decimal("0.00"), le=Decimal("100.00"), description="Standard reference discount %"
    )
    max_discount_pct: Decimal = Field(
        Decimal("0.00"), ge=Decimal("0.00"), le=Decimal("100.00"), description="Maximum allowable discount %"
    )
    priority: int = Field(100, description="Priority ranking (lower integer = higher priority)")
    effective_from: Optional[datetime] = Field(None, description="Policy effective start timestamp")
    effective_to: Optional[datetime] = Field(None, description="Optional policy effective end timestamp")
    is_active: bool = Field(True, description="Administrative active flag")


class DiscountPolicyCreate(DiscountPolicyBase):
    pass


class DiscountPolicyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    customer_tier_id: Optional[int] = None
    product_category_id: Optional[int] = None
    product_id: Optional[int] = None
    standard_discount_pct: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("100.00"))
    max_discount_pct: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("100.00"))
    priority: Optional[int] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    is_active: Optional[bool] = None


class DiscountPolicyRead(DiscountPolicyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    customer_tier: Optional[CustomerTierRead] = None
    product_category: Optional[ProductCategoryRead] = None
    product: Optional[ProductRead] = None

    model_config = ConfigDict(from_attributes=True)


class DiscountPolicyResolutionRead(BaseModel):
    applicable_policy: Optional[DiscountPolicyRead] = None
    specificity_level: Optional[str] = Field(
        None, description="Resolved specificity tier (e.g., 'tier+product', 'product', 'tier+category', 'category', 'tier', 'global')"
    )
