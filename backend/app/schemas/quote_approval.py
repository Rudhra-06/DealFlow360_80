from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserRead


class QuoteApprovalTriggerRead(BaseModel):
    id: int
    approval_step_id: int
    approval_policy_id: Optional[int] = None
    trigger_code: str
    actual_value: Optional[Decimal] = None
    threshold_value: Optional[Decimal] = None
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuoteApprovalStepRead(BaseModel):
    id: int
    quotation_id: int
    approval_round: int
    sequence: int
    approval_role: str
    status: str
    decided_by_user_id: Optional[int] = None
    decision_reason: Optional[str] = None
    requested_at: datetime
    decided_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    decided_by_user: Optional[UserRead] = None
    triggers: List[QuoteApprovalTriggerRead] = []

    model_config = ConfigDict(from_attributes=True)


class ApprovalDecisionRequest(BaseModel):
    reason: Optional[str] = Field(None, description="Reason for decision (mandatory for reject and return)")


class QuoteSubmissionResponse(BaseModel):
    quotation_id: int
    status: str
    requires_approval: bool
    approval_round: int
    required_roles: List[str]
    steps: List[QuoteApprovalStepRead] = []
    message: str
