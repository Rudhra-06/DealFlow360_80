import sys
import uuid
from pathlib import Path
import pytest
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.jwt import decode_access_token
from app.repositories.role import RoleRepository
from app.schemas.role import RoleCreateInternal
from app.services.auth import AuthenticationService
from app.services.user import UserService
from app.services.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
)




@pytest.fixture
async def test_role(db_session: AsyncSession):
    """Provides a temporary test role committed in database for auth service testing."""
    role_repo = RoleRepository()
    role_name = f"TEST_AUTH_ROLE_{uuid.uuid4().hex[:6]}"
    role_input = RoleCreateInternal(
        name=role_name,
        description="Role for auth service testing",
    )
    role = await role_repo.create_role(db_session, role_input)
    await db_session.commit()
    return role


@pytest.mark.anyio
async def test_authenticate_user_success_and_email_normalization(db_session: AsyncSession, test_role):
    """Verify authenticate_user succeeds with valid credentials and normalizes input email."""
    user_service = UserService(db_session)
    auth_service = AuthenticationService(db_session)

    uid = uuid.uuid4().hex[:6]
    raw_email = f"  AUTH-SUCCESS-{uid}@EXAMPLE.COM  "
    plain_password = "SecretAuthPassword123!"

    created_user = await user_service.create_user(
        email=raw_email,
        full_name="Auth Success User",
        plain_password=plain_password,
        role_id=test_role.id,
    )

    # Authenticate using un-normalized email with extra spaces and uppercase
    authenticated_user = await auth_service.authenticate_user(
        email=f"  auth-success-{uid}@example.com  ",
        plain_password=plain_password,
    )

    assert authenticated_user is not None
    assert authenticated_user.id == created_user.id
    assert authenticated_user.email == f"auth-success-{uid}@example.com"

    # Test token creation for authenticated user
    token = auth_service.create_user_access_token(authenticated_user)
    payload = decode_access_token(token)
    assert payload.sub == str(created_user.id)


@pytest.mark.anyio
async def test_authenticate_user_wrong_password_raises_invalid_credentials(db_session: AsyncSession, test_role):
    """Verify authenticate_user raises InvalidCredentialsError when password is incorrect."""
    user_service = UserService(db_session)
    auth_service = AuthenticationService(db_session)

    uid = uuid.uuid4().hex[:6]
    email = f"auth-wrong-{uid}@example.com"
    correct_password = "CorrectPassword123!"
    wrong_password = "WrongPassword456!"

    await user_service.create_user(
        email=email,
        full_name="Auth Wrong Pass User",
        plain_password=correct_password,
        role_id=test_role.id,
    )

    with pytest.raises(InvalidCredentialsError) as exc_info:
        await auth_service.authenticate_user(
            email=email,
            plain_password=wrong_password,
        )

    assert "invalid email or password" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_authenticate_user_unknown_email_raises_invalid_credentials(db_session: AsyncSession):
    """Verify authenticate_user raises SAME InvalidCredentialsError for non-existent email."""
    auth_service = AuthenticationService(db_session)
    unknown_email = f"non_existent_{uuid.uuid4().hex[:6]}@example.com"

    with pytest.raises(InvalidCredentialsError) as exc_info:
        await auth_service.authenticate_user(
            email=unknown_email,
            plain_password="SomePassword123!",
        )

    # Must be exact same user-enumeration safe message
    assert "invalid email or password" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_authenticate_user_inactive_user_raises_inactive_error(db_session: AsyncSession, test_role):
    """Verify authenticate_user raises InactiveUserError when user account is inactive."""
    user_service = UserService(db_session)
    auth_service = AuthenticationService(db_session)

    uid = uuid.uuid4().hex[:6]
    email = f"auth-inactive-{uid}@example.com"
    password = "InactivePassword123!"

    user = await user_service.create_user(
        email=email,
        full_name="Inactive User",
        plain_password=password,
        role_id=test_role.id,
    )

    # Set user inactive in transaction
    user.is_active = False
    await db_session.commit()

    with pytest.raises(InactiveUserError) as exc_info:
        await auth_service.authenticate_user(
            email=email,
            plain_password=password,
        )

    assert "inactive" in str(exc_info.value).lower()
