from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr

from app.schemas.role import RoleRead


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True

class UserCreateInternal(UserBase):
    """Internal schema for creating a new User record. Note: hashed_password must be pre-hashed."""

    hashed_password: str
    role_id: int


class UserRead(UserBase):
    id: int
    role_id: int
    created_at: datetime
    updated_at: datetime
    role: Optional[RoleRead] = None

    model_config = ConfigDict(from_attributes=True)
