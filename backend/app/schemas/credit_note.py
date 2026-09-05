from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class CreditNoteLineRead(BaseModel):
    id: int
    credit_note_id: int
    description: str
    quantity: Decimal
    unit_amount: Decimal
    amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreditNoteRead(BaseModel):
    id: int
    credit_note_number: str
    customer_id: int
    sales_order_id: int
    subscription_id: Optional[int] = None
    invoice_id: Optional[int] = None
    status: str
    currency: str
    amount: Decimal
    reason: Optional[str] = None
    created_at: datetime
    issued_at: datetime
    applied_at: Optional[datetime] = None
    lines: List[CreditNoteLineRead] = []

    model_config = ConfigDict(from_attributes=True)


class CreditNoteApplyRequest(BaseModel):
    invoice_id: int
