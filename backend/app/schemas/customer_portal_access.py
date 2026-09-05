from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.customer import CustomerRead
from app.schemas.user import UserRead


class CustomerPortalAccessCreate(BaseModel):
    user_id: int = Field(..., description="ID of User with CUSTOMER role")
    customer_id: int = Field(..., description="ID of Customer account")
    is_active: bool = Field(True, description="Active status flag")


class CustomerPortalAccessUpdate(BaseModel):
    is_active: Optional[bool] = Field(None, description="Updated active status flag")


class CustomerPortalAccessRead(BaseModel):
    id: int
    user_id: int
    customer_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    user: Optional[UserRead] = None
    customer: Optional[CustomerRead] = None

    model_config = ConfigDict(from_attributes=True)
