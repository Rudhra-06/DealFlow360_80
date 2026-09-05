from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import ExpiredTokenError, InvalidTokenError, decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository

http_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency extracting Bearer token and fetching authenticated active User.
    
    Decodes the JWT access token from the Authorization header, validates its expiration and signature,
    safely converts the subject claim to an integer user ID, and re-validates the user and role state
    directly from PostgreSQL.

    Args:
        credentials: Bearer token credentials injected by HTTPBearer.
        db: AsyncSession database dependency.

    Returns:
        Authenticated active User ORM instance with loaded Role relationship.

    Raises:
        HTTPException(401): If token is missing, invalid, expired, or user does not exist.
        HTTPException(403): If authenticated user account is inactive.
    """
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except ExpiredTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(payload.sub)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository()
    user = await user_repo.get_by_id(db, user_id, load_role=True)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user
