from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.auth import AuthenticationService
from app.services.exceptions import InactiveUserError, InvalidCredentialsError

auth_router = APIRouter()


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate User and Issue JWT Access Token",
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticates user credentials and returns a signed JWT access token.
    
    Accepts email and plain-text password, delegates validation to AuthenticationService,
    and returns a Bearer access token upon successful verification.
    """
    auth_service = AuthenticationService(db)
    try:
        user = await auth_service.authenticate_user(body.email, body.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InactiveUserError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = auth_service.create_user_access_token(user)
    return TokenResponse(access_token=access_token, token_type="bearer")


@auth_router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated Current User Profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Returns the authenticated active user profile and role details.
    
    Requires a valid Bearer JWT access token in the Authorization header.
    Re-validates account status and retrieves current role directly from PostgreSQL.
    """
    return current_user
