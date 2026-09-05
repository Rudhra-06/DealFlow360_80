from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import jwt

from app.core.config import settings
from app.schemas.auth import TokenPayload


class TokenError(Exception):
    """Base exception for JWT operations."""
    pass


class InvalidTokenError(TokenError):
    """Raised when a JWT is malformed, has invalid signature, or missing claims."""
    pass


class ExpiredTokenError(InvalidTokenError):
    """Raised when a JWT has expired."""
    pass



def create_access_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generates a signed JWT access token containing standard claims.
    
    Args:
        subject: User primary key ID or unique subject string.
        expires_delta: Optional custom duration before expiration.

    Returns:
        Encoded JWT token string.
    """
    now = datetime.now(timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    claims = {
        "sub": str(subject),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    encoded_jwt = jwt.encode(
        claims,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> TokenPayload:
    """Decodes and validates a signed JWT access token.
    
    Args:
        token: Candidate JWT string.

    Returns:
        Validated TokenPayload schema.

    Raises:
        ExpiredTokenError: If token expiration (exp) timestamp has passed.
        InvalidTokenError: If token signature fails, format is malformed, or claims are invalid.
    """
    if not token or not isinstance(token, str):
        raise InvalidTokenError("Token must be a non-empty string.")

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as e:
        raise ExpiredTokenError("Token has expired.") from e
    except jwt.PyJWTError as e:
        raise InvalidTokenError("Invalid token signature or payload.") from e

    sub = payload.get("sub")
    token_type = payload.get("type")

    if not sub or token_type != "access":
        raise InvalidTokenError("Token payload missing required access claims.")

    return TokenPayload(
        sub=str(sub),
        type=token_type,
        iat=payload.get("iat"),
        exp=payload.get("exp"),
    )
