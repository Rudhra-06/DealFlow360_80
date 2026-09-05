from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class TokenPayload(BaseModel):
    """Schema representing validated JWT claim payload."""

    sub: str
    type: str = "access"
    iat: Optional[int] = None
    exp: Optional[int] = None

    model_config = ConfigDict(extra="ignore")


class LoginRequest(BaseModel):
    """Schema for user authentication request."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for successful authentication token response."""

    access_token: str
    token_type: str = "bearer"
