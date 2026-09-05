from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CustomerTierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class CustomerTierCreate(CustomerTierBase):
    is_active: bool = True


class CustomerTierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerTierRead(CustomerTierBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
