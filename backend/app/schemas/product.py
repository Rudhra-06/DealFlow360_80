from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product_category import ProductCategoryRead


class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category_id: int
    list_price: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    cost_price: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    currency: str = Field("USD", min_length=3, max_length=3)
    unit_of_measure: str = Field("EA", min_length=1, max_length=20)


class ProductCreate(ProductBase):
    is_active: bool = True


class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category_id: Optional[int] = None
    list_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    cost_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    unit_of_measure: Optional[str] = Field(None, min_length=1, max_length=20)
    is_active: Optional[bool] = None


class ProductRead(ProductBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: Optional[ProductCategoryRead] = None

    model_config = ConfigDict(from_attributes=True)
