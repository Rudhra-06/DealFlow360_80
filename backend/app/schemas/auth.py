from typing import Optional
from pydantic import BaseModel, ConfigDict


class TokenPayload(BaseModel):
    """Schema representing validated JWT claim payload."""

    sub: str
    type: str = "access"
    iat: Optional[int] = None
    exp: Optional[int] = None

    model_config = ConfigDict(extra="ignore")
