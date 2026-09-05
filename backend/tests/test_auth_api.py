import sys
import uuid
from datetime import timedelta
from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.db.session import get_db
from app.core.jwt import create_access_token
from app.repositories.role import RoleRepository
from app.schemas.role import RoleCreateInternal
from app.services.user import UserService


@pytest.fixture
async def async_client(db_session: AsyncSession):
    """Provides an AsyncClient bound to the test event loop with DB session override."""
    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_login_success(db_session: AsyncSession, async_client: AsyncClient):
    """Verify POST /api/v1/auth/login returns JWT token on valid credentials."""
    role_repo = RoleRepository()
    role = await role_repo.create_role(
        db_session,
        RoleCreateInternal(name=f"LOGIN_ROLE_{uuid.uuid4().hex[:6]}")
    )
    await db_session.commit()

    user_service = UserService(db_session)
    email = f"login-user-{uuid.uuid4().hex[:6]}@example.com"
    password = "SecurePassword123!"
    user = await user_service.create_user(
        email=email,
        full_name="Login Test User",
        plain_password=password,
        role_id=role.id,
    )

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


@pytest.mark.anyio
async def test_login_email_normalization(db_session: AsyncSession, async_client: AsyncClient):
    """Verify POST /api/v1/auth/login handles un-normalized emails cleanly."""
    role_repo = RoleRepository()
    role = await role_repo.create_role(
        db_session,
        RoleCreateInternal(name=f"NORM_ROLE_{uuid.uuid4().hex[:6]}")
    )
    await db_session.commit()

    user_service = UserService(db_session)
    uid = uuid.uuid4().hex[:6]
    clean_email = f"norm-user-{uid}@example.com"
    password = "SecurePassword123!"
    await user_service.create_user(
        email=clean_email,
        full_name="Norm Test User",
        plain_password=password,
        role_id=role.id,
    )

    # Supply raw un-normalized email with mixed case and padding
    unnormalized_email = f"  NORM-USER-{uid}@EXAMPLE.COM  "
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": unnormalized_email, "password": password}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.anyio
async def test_login_wrong_password(db_session: AsyncSession, async_client: AsyncClient):
    """Verify POST /api/v1/auth/login returns HTTP 401 for incorrect password."""
    role_repo = RoleRepository()
    role = await role_repo.create_role(
        db_session,
        RoleCreateInternal(name=f"WP_ROLE_{uuid.uuid4().hex[:6]}")
    )
    await db_session.commit()

    user_service = UserService(db_session)
    email = f"wp-user-{uuid.uuid4().hex[:6]}@example.com"
    await user_service.create_user(
        email=email,
        full_name="Wrong Pass User",
        plain_password="CorrectPassword123!",
        role_id=role.id,
    )

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword123!"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


@pytest.mark.anyio
async def test_login_unknown_email(db_session: AsyncSession, async_client: AsyncClient):
    """Verify POST /api/v1/auth/login returns HTTP 401 for non-existent email (anti-user-enumeration)."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "AnyPassword123!"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


@pytest.mark.anyio
async def test_login_inactive_user(db_session: AsyncSession, async_client: AsyncClient):
    """Verify POST /api/v1/auth/login returns HTTP 403 for inactive user."""
    role_repo = RoleRepository()
    role = await role_repo.create_role(
        db_session,
        RoleCreateInternal(name=f"INACT_ROLE_{uuid.uuid4().hex[:6]}")
    )
    await db_session.commit()

    user_service = UserService(db_session)
    email = f"inact-user-{uuid.uuid4().hex[:6]}@example.com"
    password = "SecurePassword123!"
    user = await user_service.create_user(
        email=email,
        full_name="Inactive User",
        plain_password=password,
        role_id=role.id,
    )
    user.is_active = False
    await db_session.commit()

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "User account is inactive"


@pytest.mark.anyio
async def test_auth_me_success(db_session: AsyncSession, async_client: AsyncClient):
    """Verify GET /api/v1/auth/me returns UserRead schema without hashed_password."""
    role_repo = RoleRepository()
    role_name = f"ME_ROLE_{uuid.uuid4().hex[:6]}"
    role = await role_repo.create_role(
        db_session,
        RoleCreateInternal(name=role_name)
    )
    await db_session.commit()

    user_service = UserService(db_session)
    email = f"me-user-{uuid.uuid4().hex[:6]}@example.com"
    user = await user_service.create_user(
        email=email,
        full_name="Me User Test",
        plain_password="SecurePassword123!",
        role_id=role.id,
    )

    # Login to obtain token
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"}
    )
    token = login_resp.json()["access_token"]

    # Request /me with Bearer token
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["email"] == email
    assert data["full_name"] == "Me User Test"
    assert data["is_active"] is True
    assert data["role_id"] == role.id
    assert data["role"]["name"] == role_name
    assert "hashed_password" not in data


@pytest.mark.anyio
async def test_auth_me_missing_token(db_session: AsyncSession, async_client: AsyncClient):
    """Verify GET /api/v1/auth/me returns authentication error when header is missing."""
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_auth_me_malformed_token(db_session: AsyncSession, async_client: AsyncClient):
    """Verify GET /api/v1/auth/me returns HTTP 401 for malformed JWT token."""
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.anyio
async def test_auth_me_expired_token(db_session: AsyncSession, async_client: AsyncClient):
    """Verify GET /api/v1/auth/me returns HTTP 401 when access token is expired."""
    expired_token = create_access_token(
        subject="123",
        expires_delta=timedelta(seconds=-10)
    )
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Access token has expired"


@pytest.mark.anyio
async def test_auth_me_nonexistent_user(db_session: AsyncSession, async_client: AsyncClient):
    """Verify GET /api/v1/auth/me returns HTTP 401 when token subject does not exist in DB."""
    token = create_access_token(subject="999999")
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.anyio
async def test_auth_me_inactive_current_user(db_session: AsyncSession, async_client: AsyncClient):
    """Verify GET /api/v1/auth/me returns HTTP 403 when active user is deactivated after token issue."""
    role_repo = RoleRepository()
    role = await role_repo.create_role(
        db_session,
        RoleCreateInternal(name=f"DEACT_ROLE_{uuid.uuid4().hex[:6]}")
    )
    await db_session.commit()

    user_service = UserService(db_session)
    email = f"deact-user-{uuid.uuid4().hex[:6]}@example.com"
    user = await user_service.create_user(
        email=email,
        full_name="Deactivated User",
        plain_password="SecurePassword123!",
        role_id=role.id,
    )

    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"}
    )
    token = login_resp.json()["access_token"]

    # Deactivate user after token creation
    user.is_active = False
    await db_session.commit()

    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "User account is inactive"
