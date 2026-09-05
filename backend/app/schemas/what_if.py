from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class LineOverrideItem(BaseModel):
    line_id: int = Field(..., description="ID of quotation line to hypothetically override")
    quantity: Optional[Decimal] = Field(None, gt=Decimal("0.000"), description="Simulated quantity override")
    line_discount_pct: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00"), description="Simulated line discount % override"
    )


class WhatIfRequest(BaseModel):
    order_discount_pct: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00"), description="Simulated order discount % override"
    )
    payment_terms_days: Optional[int] = Field(None, ge=0, description="Simulated payment terms days override")
    line_overrides: Optional[List[LineOverrideItem]] = Field(None, description="Hypothetical line-level overrides")


class WhatIfStateSnapshotRead(BaseModel):
    gross_subtotal: Decimal
    discount_amount: Decimal
    net_total: Decimal
    total_cost: Decimal
    margin_amount: Decimal
    margin_pct: Decimal
    weighted_effective_discount_pct: Decimal
    blended_risk_score: Decimal
    risk_level: str
    required_approval_roles: List[str]
    projected_status: str


class WhatIfDeltasRead(BaseModel):
    net_total_delta: Decimal
    margin_amount_delta: Decimal
    margin_pct_delta: Decimal
    risk_score_delta: Decimal


class WhatIfResponse(BaseModel):
    quotation_id: int
    persisted: bool = False
    before: WhatIfStateSnapshotRead
    after: WhatIfStateSnapshotRead
    changes: WhatIfDeltasRead
    new_approval_required: bool
    risk_reasons: List[dict] = []

    model_config = ConfigDict(from_attributes=True)
