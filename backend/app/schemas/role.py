from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleRead(RoleBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
