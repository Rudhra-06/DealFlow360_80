from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserRead


class QuoteNegotiationMessageCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="Comment or question text")
    quotation_line_id: Optional[int] = Field(None, description="Optional quotation line ID")
    message_type: Optional[str] = Field("COMMENT", description="Message type (COMMENT or LINE_QUESTION)")


class QuoteNegotiationMessageRead(BaseModel):
    id: int
    quotation_id: int
    quote_version_id: Optional[int] = None
    quotation_line_id: Optional[int] = None
    author_user_id: int
    message_type: str
    message: str
    is_customer_visible: bool
    created_at: datetime

    author_user: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)


class QuoteNegotiationLineChangeCreate(BaseModel):
    quotation_line_id: int = Field(..., description="ID of line to modify")
    requested_quantity: Optional[Decimal] = Field(None, gt=Decimal("0.000"), description="Requested line quantity")
    requested_line_discount_pct: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00"), description="Requested line discount %"
    )


class QuoteNegotiationLineChangeRead(BaseModel):
    id: int
    negotiation_request_id: int
    quotation_line_id: int
    requested_quantity: Optional[Decimal] = None
    requested_line_discount_pct: Optional[Decimal] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuoteNegotiationRequestCreate(BaseModel):
    request_type: str = Field("COUNTER_OFFER", description="COUNTER_OFFER or CHANGE_REQUEST")
    message: Optional[str] = Field(None, max_length=5000, description="Optional explanation or message")
    requested_order_discount_pct: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00"), description="Requested overall order discount %"
    )
    requested_payment_terms_days: Optional[int] = Field(None, ge=0, description="Requested payment terms in days")
    line_changes: List[QuoteNegotiationLineChangeCreate] = Field(default_factory=list, description="Requested line-level modifications")


class QuoteNegotiationRequestReject(BaseModel):
    resolution_reason: Optional[str] = Field(None, max_length=1000, description="Reason for rejecting negotiation request")
    rejection_reason: Optional[str] = Field(None, max_length=1000, description="Alias for resolution_reason")


class QuoteNegotiationRequestRead(BaseModel):
    id: int
    quotation_id: int
    base_quote_version_id: int
    requested_by_user_id: int
    request_type: str
    status: str
    message: Optional[str] = None

    requested_order_discount_pct: Optional[Decimal] = None
    requested_payment_terms_days: Optional[int] = None

    resolved_at: Optional[datetime] = None
    resolved_by_user_id: Optional[int] = None
    resolution_reason: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    line_changes: List[QuoteNegotiationLineChangeRead] = Field(default_factory=list)
    requested_by_user: Optional[UserRead] = None
    resolved_by_user: Optional[UserRead] = None

    @property
    def rejection_reason(self) -> Optional[str]:
        return self.resolution_reason

    model_config = ConfigDict(from_attributes=True)
