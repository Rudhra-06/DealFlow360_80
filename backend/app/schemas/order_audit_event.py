from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserRead


class OrderAuditEventRead(BaseModel):
    id: int
    sales_order_id: int
    actor_user_id: Optional[int] = None
    event_type: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    reason: Optional[str] = None
    event_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    actor_user: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)
