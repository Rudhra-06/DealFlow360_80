from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductRead


class RecommendationRuleBase(BaseModel):
    source_product_id: int = Field(..., description="ID of anchor/trigger Product")
    suggested_product_id: int = Field(..., description="ID of recommended target Product")
    affinity_score: Decimal = Field(
        Decimal("1.00"), ge=Decimal("0.00"), description="Co-purchase affinity score (>= 0)"
    )
    recommended_qty: Decimal = Field(
        Decimal("1.000"), gt=Decimal("0.000"), description="Recommended quantity (> 0)"
    )
    is_promoted: bool = Field(False, description="Flag promoting this recommendation to top rank")
    promotion_label: Optional[str] = Field(None, description="Display label for promotion e.g. 'Featured Upsell'")
    min_margin_pct: Optional[Decimal] = Field(
        None, ge=Decimal("-100.00"), le=Decimal("100.00"), description="Minimum acceptable margin % threshold"
    )
    priority: int = Field(100, description="Priority ranking (lower = higher priority)")
    effective_from: Optional[datetime] = Field(None, description="Rule effective start timestamp")
    effective_to: Optional[datetime] = Field(None, description="Optional rule effective end timestamp")
    is_active: bool = Field(True, description="Administrative active flag")


class RecommendationRuleCreate(RecommendationRuleBase):
    pass


class RecommendationRuleUpdate(BaseModel):
    source_product_id: Optional[int] = None
    suggested_product_id: Optional[int] = None
    affinity_score: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    recommended_qty: Optional[Decimal] = Field(None, gt=Decimal("0.000"))
    is_promoted: Optional[bool] = None
    promotion_label: Optional[str] = None
    min_margin_pct: Optional[Decimal] = Field(None, ge=Decimal("-100.00"), le=Decimal("100.00"))
    priority: Optional[int] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    is_active: Optional[bool] = None


class RecommendationRuleRead(RecommendationRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    source_product: Optional[ProductRead] = None
    suggested_product: Optional[ProductRead] = None

    model_config = ConfigDict(from_attributes=True)


class QuoteRecommendationRead(BaseModel):
    rule_id: int
    source_product_id: int
    suggested_product_id: int
    recommended_qty: Decimal
    standard_discount_used: Decimal
    unit_list_price: Decimal
    unit_cost: Decimal

    incremental_revenue: Decimal
    incremental_cost: Decimal
    incremental_margin_amount: Decimal
    incremental_margin_pct: Decimal

    projected_quote_net_total: Decimal
    projected_quote_margin_pct: Decimal

    is_promoted: bool
    promotion_label: Optional[str] = None
    affinity_score: Decimal
    priority: int
    explanation: str

    suggested_product: Optional[ProductRead] = None
