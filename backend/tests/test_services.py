import sys
import uuid
import pytest
from pathlib import Path
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.security import verify_password
from app.repositories.role import RoleRepository
from app.schemas.role import RoleCreateInternal
from app.services.role import RoleService
from app.services.user import UserService
from app.services.exceptions import RoleNotFoundError, UserAlreadyExistsError




@pytest.mark.anyio
async def test_role_service_methods(db_session: AsyncSession):
    """Verify RoleService methods get_role_by_id, get_role_by_name, list_roles."""
    role_repo = RoleRepository()
    test_role_name = f"TEST_SERVICE_ROLE_{uuid.uuid4().hex[:6]}"
    
    created_role = await role_repo.create_role(
        db_session,
        RoleCreateInternal(name=test_role_name, description="Test role description")
    )
    await db_session.commit()
    role_id = created_role.id

    role_service = RoleService(db_session)
    by_id = await role_service.get_role_by_id(role_id)
    assert by_id is not None
    assert by_id.name == test_role_name

    by_name = await role_service.get_role_by_name(test_role_name)
    assert by_name is not None
    assert by_name.id == role_id

    all_roles = await role_service.list_roles()
    assert len(all_roles) > 0


@pytest.mark.anyio
async def test_user_service_create_user_success_and_email_normalization(db_session: AsyncSession):
    """Verify UserService.create_user normalizes email, hashes password, and persists user."""
    role_repo = RoleRepository()
    role_name = f"TEST_SRV_ROLE_{uuid.uuid4().hex[:6]}"
    role = await role_repo.create_role(
        db_session,
        RoleCreateInternal(name=role_name, description="Test role")
    )
    await db_session.commit()

    user_service = UserService(db_session)
    uid = uuid.uuid4().hex[:6]
    raw_email = f"  SRV-USER-{uid}@EXAMPLE.COM  "
    plain_pass = "SecurePass123!"

    user = await user_service.create_user(
        email=raw_email,
        full_name="Service User Test",
        plain_password=plain_pass,
        role_id=role.id,
    )

    assert user.id is not None
    assert user.email == f"srv-user-{uid}@example.com"
    assert user.full_name == "Service User Test"
    assert user.hashed_password != plain_pass
    assert verify_password(plain_pass, user.hashed_password) is True


@pytest.mark.anyio
async def test_user_service_duplicate_email_raises_error(db_session: AsyncSession):
    """Verify UserService.create_user raises UserAlreadyExistsError for duplicate emails."""
    role_repo = RoleRepository()
    role_name = f"TEST_DUP_ROLE_{uuid.uuid4().hex[:6]}"
    role = await role_repo.create_role(
        db_session,
        RoleCreateInternal(name=role_name, description="Test role")
    )
    await db_session.commit()

    user_service = UserService(db_session)
    uid = uuid.uuid4().hex[:6]
    duplicate_email = f"srv-dup-{uid}@example.com"

    await user_service.create_user(
        email=duplicate_email,
        full_name="Duplicate User Test 1",
        plain_password="AnotherPassword123!",
        role_id=role.id,
    )

    with pytest.raises(UserAlreadyExistsError) as exc_info:
        await user_service.create_user(
            email=f"  SRV-DUP-{uid}@EXAMPLE.COM  ",
            full_name="Duplicate User Test 2",
            plain_password="AnotherPassword123!",
            role_id=role.id,
        )
    assert "already exists" in str(exc_info.value)


@pytest.mark.anyio
async def test_user_service_invalid_role_id_raises_error(db_session: AsyncSession):
    """Verify UserService.create_user raises RoleNotFoundError when referencing missing role_id."""
    user_service = UserService(db_session)
    invalid_role_id = 999999

    with pytest.raises(RoleNotFoundError) as exc_info:
        await user_service.create_user(
            email=f"invalid-role-{uuid.uuid4().hex[:6]}@example.com",
            full_name="Invalid Role Test",
            plain_password="Password123!",
            role_id=invalid_role_id,
        )
    assert "Role with ID 999999 not found" in str(exc_info.value)
