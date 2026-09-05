from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class NotificationRead(BaseModel):
    id: int
    user_id: int
    notification_type: str
    title: str
    message: str
    quotation_id: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationReadPatch(BaseModel):
    is_read: bool = Field(True, description="Flag indicating if notification has been read")


class UserDeviceCreate(BaseModel):
    device_token: str = Field(..., min_length=1, max_length=500, description="Unique FCM device token")
    platform: Optional[str] = Field(None, description="Device platform (e.g., ios, android, web)")


class UserDeviceRead(BaseModel):
    id: int
    user_id: int
    device_token: str
    platform: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
