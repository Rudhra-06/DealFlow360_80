import sys
import uuid
from pathlib import Path

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.api.dependencies.rbac import require_roles
from app.core.jwt import create_access_token
from app.core.roles import RoleName
from app.db.session import get_db
from app.models.user import User
from app.repositories.role import RoleRepository
from app.schemas.role import RoleCreateInternal
from app.services.user import UserService

# Test-only FastAPI application to test RBAC dependency in isolation
test_app = FastAPI(title="RBAC Isolated Test App")


@test_app.get("/test/role-a-only")
async def role_a_only(user: User = Depends(require_roles("TEST_ROLE_A"))):
    return {"user_id": user.id, "email": user.email, "role": user.role.name}


@test_app.get("/test/role-b-only")
async def role_b_only(user: User = Depends(require_roles("TEST_ROLE_B"))):
    return {"user_id": user.id, "email": user.email, "role": user.role.name}


@test_app.get("/test/multi-role")
async def multi_role(
    user: User = Depends(require_roles("TEST_ROLE_A", "TEST_ROLE_B"))
):
    return {"user_id": user.id, "email": user.email, "role": user.role.name}


@test_app.get("/test/manager-only")
async def manager_only(
    user: User = Depends(require_roles(RoleName.SALES_MANAGER))
):
    return {"user_id": user.id, "email": user.email, "role": user.role.name}


@test_app.get("/test/admin-or-manager")
async def admin_or_manager(
    user: User = Depends(require_roles(RoleName.ADMIN, RoleName.SALES_MANAGER))
):
    return {"user_id": user.id, "email": user.email, "role": user.role.name}


@pytest.fixture
async def rbac_client(db_session: AsyncSession):
    """Provides an AsyncClient bound to test_app with DB session override."""
    async def _get_db_override():
        yield db_session

    test_app.dependency_overrides[get_db] = _get_db_override
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://testserver",
    ) as ac:
        yield ac
    test_app.dependency_overrides.clear()


async def get_or_create_role(db_session: AsyncSession, role_name: str):
    role_repo = RoleRepository()
    role = await role_repo.get_by_name(db_session, role_name)
    if not role:
        role = await role_repo.create_role(
            db_session, RoleCreateInternal(name=role_name)
        )
        await db_session.commit()
    return role


@pytest.mark.anyio
async def test_allowed_role_returns_200(
    db_session: AsyncSession, rbac_client: AsyncClient
):
    """Verify authenticated user with allowed role is granted access (200)."""
    role = await get_or_create_role(db_session, "TEST_ROLE_A")

    user_service = UserService(db_session)
    email = f"user-a-{uuid.uuid4().hex[:6]}@example.com"
    user = await user_service.create_user(
        email=email,
        full_name="User A",
        plain_password="Password123!",
        role_id=role.id,
    )
    token = create_access_token(subject=str(user.id))

    response = await rbac_client.get(
        "/test/role-a-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user.id
    assert data["email"] == email


@pytest.mark.anyio
async def test_wrong_role_returns_403(
    db_session: AsyncSession, rbac_client: AsyncClient
):
    """Verify authenticated user with unauthorized role receives HTTP 403 Forbidden."""
    role_a = await get_or_create_role(db_session, "TEST_ROLE_A")

    user_service = UserService(db_session)
    user = await user_service.create_user(
        email=f"user-wrong-{uuid.uuid4().hex[:6]}@example.com",
        full_name="Wrong Role User",
        plain_password="Password123!",
        role_id=role_a.id,
    )
    token = create_access_token(subject=str(user.id))

    response = await rbac_client.get(
        "/test/role-b-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


@pytest.mark.anyio
async def test_multiple_allowed_roles_success(
    db_session: AsyncSession, rbac_client: AsyncClient
):
    """Verify require_roles grants access if user matches any one of multiple allowed roles (OR logic)."""
    role_b = await get_or_create_role(db_session, "TEST_ROLE_B")

    user_service = UserService(db_session)
    user = await user_service.create_user(
        email=f"user-multi-{uuid.uuid4().hex[:6]}@example.com",
        full_name="Multi Role User",
        plain_password="Password123!",
        role_id=role_b.id,
    )
    token = create_access_token(subject=str(user.id))

    response = await rbac_client.get(
        "/test/multi-role", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "TEST_ROLE_B"


@pytest.mark.anyio
async def test_missing_token_returns_401(rbac_client: AsyncClient):
    """Verify unauthenticated request without token fails with 401 from get_current_user."""
    response = await rbac_client.get("/test/role-a-only")
    assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_invalid_token_returns_401(rbac_client: AsyncClient):
    """Verify invalid token fails with 401 from authentication layer, not 403."""
    response = await rbac_client.get(
        "/test/role-a-only",
        headers={"Authorization": "Bearer malformed.invalid.token"},
    )
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.anyio
async def test_inactive_user_returns_403(
    db_session: AsyncSession, rbac_client: AsyncClient
):
    """Verify inactive user is blocked with HTTP 403 before role authorization."""
    role_a = await get_or_create_role(db_session, "TEST_ROLE_A")

    user_service = UserService(db_session)
    user = await user_service.create_user(
        email=f"user-inact-{uuid.uuid4().hex[:6]}@example.com",
        full_name="Inactive RBAC User",
        plain_password="Password123!",
        role_id=role_a.id,
    )
    user.is_active = False
    await db_session.commit()

    token = create_access_token(subject=str(user.id))
    response = await rbac_client.get(
        "/test/role-a-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "User account is inactive"


@pytest.mark.anyio
async def test_role_changed_after_token_issuance(
    db_session: AsyncSession, rbac_client: AsyncClient
):
    """Verify database role changes take effect immediately using an old token without reissuance."""
    role_a = await get_or_create_role(db_session, "TEST_ROLE_A")
    role_b = await get_or_create_role(db_session, "TEST_ROLE_B")

    user_service = UserService(db_session)
    user = await user_service.create_user(
        email=f"user-rolechange-{uuid.uuid4().hex[:6]}@example.com",
        full_name="Role Change User",
        plain_password="Password123!",
        role_id=role_a.id,
    )
    token = create_access_token(subject=str(user.id))

    # Token works for ROLE_A
    res1 = await rbac_client.get(
        "/test/role-a-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert res1.status_code == 200

    # Change user role in DB to ROLE_B and expire session cache so identity map reloads fresh role
    user.role_id = role_b.id
    await db_session.commit()
    db_session.expire_all()

    # Using SAME token, request for ROLE_A now fails with 403
    res2 = await rbac_client.get(
        "/test/role-a-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert res2.status_code == 403

    # Using SAME token, request for ROLE_B now succeeds with 200
    res3 = await rbac_client.get(
        "/test/role-b-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert res3.status_code == 200
    assert res3.json()["role"] == "TEST_ROLE_B"


@pytest.mark.anyio
async def test_admin_is_not_magic(
    db_session: AsyncSession, rbac_client: AsyncClient
):
    """Verify ADMIN role does not bypass authorization unless explicitly listed in allowed roles."""
    admin_role = await get_or_create_role(db_session, RoleName.ADMIN)

    user_service = UserService(db_session)
    admin_user = await user_service.create_user(
        email=f"admin-{uuid.uuid4().hex[:6]}@example.com",
        full_name="Admin User",
        plain_password="Password123!",
        role_id=admin_role.id,
    )
    token = create_access_token(subject=str(admin_user.id))

    # Route requiring only SALES_MANAGER -> 403 (No magic ADMIN bypass)
    res_mgr = await rbac_client.get(
        "/test/manager-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert res_mgr.status_code == 403
    assert res_mgr.json()["detail"] == "Insufficient permissions"

    # Route explicitly allowing ADMIN or SALES_MANAGER -> 200
    res_admin_or_mgr = await rbac_client.get(
        "/test/admin-or-manager", headers={"Authorization": f"Bearer {token}"}
    )
    assert res_admin_or_mgr.status_code == 200
    assert res_admin_or_mgr.json()["role"] == RoleName.ADMIN

