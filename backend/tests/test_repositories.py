import sys
from pathlib import Path
import pytest
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.models.role import Role
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.schemas.role import RoleCreateInternal
from app.schemas.user import UserCreateInternal


@pytest.fixture
async def db_session():
    """Provides an isolated AsyncSession using NullPool that rolls back all operations after each test."""
    test_engine = create_async_engine(settings.async_database_url, poolclass=NullPool)
    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
    await test_engine.dispose()


@pytest.fixture
async def test_role(db_session: AsyncSession) -> Role:
    """Fixture providing a temporary Role record created inside the test transaction."""
    role_repo = RoleRepository()
    role_input = RoleCreateInternal(
        name="TEST_REPOSITORY_ROLE",
        description="Isolated role for repository tests",
    )
    return await role_repo.create_role(db_session, role_input)


@pytest.mark.anyio
async def test_role_repository_get_by_name_and_id(db_session: AsyncSession, test_role: Role):
    """Verify RoleRepository get_by_name and get_by_id using test-created role."""
    role_repo = RoleRepository()

    # Fetch test role by name
    fetched_name = await role_repo.get_by_name(db_session, test_role.name)
    assert fetched_name is not None
    assert fetched_name.id == test_role.id
    assert fetched_name.name == "TEST_REPOSITORY_ROLE"

    # Fetch test role by ID
    fetched_id = await role_repo.get_by_id(db_session, test_role.id)
    assert fetched_id is not None
    assert fetched_id.name == "TEST_REPOSITORY_ROLE"


@pytest.mark.anyio
async def test_role_repository_unknown_returns_none(db_session: AsyncSession):
    """Verify RoleRepository returns None for non-existent role name/id."""
    role_repo = RoleRepository()

    unknown_name = await role_repo.get_by_name(db_session, "NON_EXISTENT_TEST_ROLE_XYZ")
    assert unknown_name is None

    unknown_id = await role_repo.get_by_id(db_session, 999999)
    assert unknown_id is None


@pytest.mark.anyio
async def test_role_repository_list_roles(db_session: AsyncSession):
    """Verify RoleRepository list_roles retrieves test roles created in current transaction."""
    role_repo = RoleRepository()
    r1 = await role_repo.create_role(db_session, RoleCreateInternal(name="TEST_LIST_ROLE_1"))
    r2 = await role_repo.create_role(db_session, RoleCreateInternal(name="TEST_LIST_ROLE_2"))

    roles = await role_repo.list_roles(db_session)
    role_names = [r.name for r in roles]

    assert r1.name in role_names
    assert r2.name in role_names


@pytest.mark.anyio
async def test_role_repository_create_role(db_session: AsyncSession):
    """Verify RoleRepository create_role flushes a new role record."""
    role_repo = RoleRepository()
    new_role_input = RoleCreateInternal(
        name="TEST_CREATION_ROLE", description="Test role creation"
    )

    created = await role_repo.create_role(db_session, new_role_input)
    assert created.id is not None
    assert created.name == "TEST_CREATION_ROLE"

    fetched = await role_repo.get_by_name(db_session, "TEST_CREATION_ROLE")
    assert fetched is not None
    assert fetched.id == created.id


@pytest.mark.anyio
async def test_user_repository_create_and_get_by_email(
    db_session: AsyncSession, test_role: Role
):
    """Verify UserRepository create_user and get_by_email operations using test role."""
    user_repo = UserRepository()

    user_input = UserCreateInternal(
        email="test_user_isolated@dealflow360.com",
        full_name="Test Isolated User",
        hashed_password="$test_hashed_password_string",
        role_id=test_role.id,
        is_active=True,
    )

    created_user = await user_repo.create_user(db_session, user_input)
    assert created_user.id is not None
    assert created_user.email == "test_user_isolated@dealflow360.com"

    fetched = await user_repo.get_by_email(db_session, "test_user_isolated@dealflow360.com")
    assert fetched is not None
    assert fetched.id == created_user.id
    assert fetched.full_name == "Test Isolated User"


@pytest.mark.anyio
async def test_user_repository_eager_loading_role(
    db_session: AsyncSession, test_role: Role
):
    """Verify UserRepository eager loading (selectinload) of Role relationship using test role."""
    user_repo = UserRepository()

    user_input = UserCreateInternal(
        email="test_eager_user@dealflow360.com",
        full_name="Test Eager User",
        hashed_password="$test_eager_hash_string",
        role_id=test_role.id,
    )
    created_user = await user_repo.create_user(db_session, user_input)

    # Fetch by email with load_role=True
    fetched = await user_repo.get_by_email(
        db_session, "test_eager_user@dealflow360.com", load_role=True
    )
    assert fetched is not None
    assert fetched.role is not None
    assert fetched.role.id == test_role.id
    assert fetched.role.name == "TEST_REPOSITORY_ROLE"

    # Fetch by ID with load_role=True
    fetched_by_id = await user_repo.get_by_id(
        db_session, created_user.id, load_role=True
    )
    assert fetched_by_id is not None
    assert fetched_by_id.role is not None
    assert fetched_by_id.role.name == "TEST_REPOSITORY_ROLE"


@pytest.mark.anyio
async def test_user_repository_unknown_email_returns_none(db_session: AsyncSession):
    """Verify UserRepository get_by_email returns None for unknown email."""
    user_repo = UserRepository()
    result = await user_repo.get_by_email(db_session, "non_existent_user@dealflow360.com")
    assert result is None


@pytest.mark.anyio
async def test_user_repository_list_and_get_by_role(
    db_session: AsyncSession, test_role: Role
):
    """Verify UserRepository list_users and get_users_by_role operations using test role."""
    user_repo = UserRepository()

    u1 = UserCreateInternal(
        email="test_group_user1@dealflow360.com",
        full_name="Test Group User 1",
        hashed_password="$test_group_hash1",
        role_id=test_role.id,
    )
    u2 = UserCreateInternal(
        email="test_group_user2@dealflow360.com",
        full_name="Test Group User 2",
        hashed_password="$test_group_hash2",
        role_id=test_role.id,
    )
    await user_repo.create_user(db_session, u1)
    await user_repo.create_user(db_session, u2)

    users_in_role = await user_repo.get_users_by_role(
        db_session, test_role.id, load_role=True
    )
    assert len(users_in_role) >= 2
    emails = [u.email for u in users_in_role]
    assert "test_group_user1@dealflow360.com" in emails
    assert "test_group_user2@dealflow360.com" in emails

    all_users = await user_repo.list_users(db_session)
    all_emails = [u.email for u in all_users]
    assert "test_group_user1@dealflow360.com" in all_emails
    assert "test_group_user2@dealflow360.com" in all_emails
