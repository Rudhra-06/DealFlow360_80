import sys
import asyncio
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.session import AsyncSessionLocal
from app.core.security import verify_password
from app.repositories.role import RoleRepository
from app.schemas.role import RoleCreateInternal
from app.services.role import RoleService
from app.services.user import UserService
from app.services.exceptions import RoleNotFoundError, UserAlreadyExistsError


def test_role_service_methods():
    """Verify RoleService methods get_role_by_id, get_role_by_name, list_roles."""
    async def _run():
        async with AsyncSessionLocal() as session:
            role_repo = RoleRepository()
            # Create an isolated temporary test role
            test_role_name = "TEST_SERVICE_ROLE"
            existing = await role_repo.get_by_name(session, test_role_name)
            if not existing:
                created_role = await role_repo.create_role(
                    session,
                    RoleCreateInternal(name=test_role_name, description="Test role description")
                )
                await session.commit()
                role_id = created_role.id
            else:
                role_id = existing.id

            role_service = RoleService(session)
            by_id = await role_service.get_role_by_id(role_id)
            assert by_id is not None
            assert by_id.name == test_role_name

            by_name = await role_service.get_role_by_name(test_role_name)
            assert by_name is not None
            assert by_name.id == role_id

            all_roles = await role_service.list_roles()
            assert len(all_roles) > 0

    asyncio.run(_run())


def test_user_service_create_user_success_and_email_normalization():
    """Verify UserService.create_user normalizes email, hashes password, and persists user."""
    async def _run():
        async with AsyncSessionLocal() as session:
            # Create test role
            role_repo = RoleRepository()
            role = await role_repo.get_by_name(session, "TEST_SERVICE_ROLE")
            if not role:
                role = await role_repo.create_role(
                    session,
                    RoleCreateInternal(name="TEST_SERVICE_ROLE", description="Test role")
                )
                await session.commit()

            user_service = UserService(session)
            raw_email = "  SERVICE-USER@EXAMPLE.COM  "
            plain_pass = "SecurePass123!"

            # Create user
            user = await user_service.create_user(
                email=raw_email,
                full_name="Service User Test",
                plain_password=plain_pass,
                role_id=role.id,
            )

            assert user.id is not None
            assert user.email == "service-user@example.com"
            assert user.full_name == "Service User Test"
            assert user.hashed_password != plain_pass
            assert verify_password(plain_pass, user.hashed_password) is True

    asyncio.run(_run())


def test_user_service_duplicate_email_raises_error():
    """Verify UserService.create_user raises UserAlreadyExistsError for duplicate emails."""
    async def _run():
        async with AsyncSessionLocal() as session:
            role_repo = RoleRepository()
            role = await role_repo.get_by_name(session, "TEST_SERVICE_ROLE")
            assert role is not None

            user_service = UserService(session)
            duplicate_email = "service-user@example.com"

            try:
                await user_service.create_user(
                    email=duplicate_email,
                    full_name="Duplicate User Test",
                    plain_password="AnotherPassword123!",
                    role_id=role.id,
                )
                assert False, "Should have raised UserAlreadyExistsError"
            except UserAlreadyExistsError as exc:
                assert "already exists" in str(exc)

    asyncio.run(_run())


def test_user_service_invalid_role_id_raises_error():
    """Verify UserService.create_user raises RoleNotFoundError when referencing missing role_id."""
    async def _run():
        async with AsyncSessionLocal() as session:
            user_service = UserService(session)
            invalid_role_id = 999999

            try:
                await user_service.create_user(
                    email="invalid-role-test@example.com",
                    full_name="Invalid Role Test",
                    plain_password="Password123!",
                    role_id=invalid_role_id,
                )
                assert False, "Should have raised RoleNotFoundError"
            except RoleNotFoundError as exc:
                assert "Role with ID 999999 not found" in str(exc)

    asyncio.run(_run())
