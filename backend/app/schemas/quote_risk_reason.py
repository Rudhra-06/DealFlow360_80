from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class QuoteRiskReasonRead(BaseModel):
    id: int
    quotation_id: int
    quotation_line_id: Optional[int] = None
    code: str
    severity: str
    message: str
    actual_value: Optional[Decimal] = None
    threshold_value: Optional[Decimal] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
