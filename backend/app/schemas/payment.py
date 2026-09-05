from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PaymentAllocationCreate(BaseModel):
    invoice_id: int
    amount: float = Field(..., gt=0.0)


class PaymentCreate(BaseModel):
    customer_id: int
    amount: float = Field(..., gt=0.0)
    currency: str = Field("USD", min_length=3, max_length=3)
    payment_method: str = Field("BANK_TRANSFER", min_length=1, max_length=50)
    reference: Optional[str] = None
    allocations: List[PaymentAllocationCreate] = Field(..., min_length=1)


class PaymentAllocationRead(BaseModel):
    id: int
    payment_id: int
    invoice_id: int
    amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentRead(BaseModel):
    id: int
    payment_number: str
    customer_id: int
    currency: str
    amount: Decimal
    payment_method: str
    reference: Optional[str] = None
    received_at: datetime
    recorded_by_user_id: int
    status: str
    created_at: datetime
    allocations: List[PaymentAllocationRead] = []

    model_config = ConfigDict(from_attributes=True)
