from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserRead


class QuoteAuditEventRead(BaseModel):
    id: int
    quotation_id: int
    actor_user_id: Optional[int] = None
    actor_user: Optional[UserRead] = None
    event_type: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    reason: Optional[str] = None
    event_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
