import sys
from pathlib import Path
from datetime import datetime, timezone

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.base import Base
from app.models.role import Role
from app.models.user import User
from app.schemas.role import RoleRead
from app.schemas.user import UserRead


def test_base_metadata_contains_roles_and_users_tables():
    """Verify that Base.metadata contains 'roles' and 'users' tables."""
    table_names = Base.metadata.tables.keys()
    assert "roles" in table_names, "'roles' table must be registered in Base.metadata"
    assert "users" in table_names, "'users' table must be registered in Base.metadata"


def test_roles_table_columns_and_constraints():
    """Verify columns and constraints on roles table in metadata."""
    roles_table = Base.metadata.tables["roles"]
    column_names = [col.name for col in roles_table.columns]
    
    assert "id" in column_names
    assert "name" in column_names
    assert "description" in column_names
    assert "created_at" in column_names

    # Check name column properties
    name_col = roles_table.columns["name"]
    assert name_col.unique is True or any(idx.unique for idx in roles_table.indexes if "name" in idx.columns)


def test_users_table_columns_and_foreign_key():
    """Verify columns and foreign keys on users table in metadata."""
    users_table = Base.metadata.tables["users"]
    column_names = [col.name for col in users_table.columns]

    assert "id" in column_names
    assert "email" in column_names
    assert "full_name" in column_names
    assert "hashed_password" in column_names
    assert "role_id" in column_names
    assert "is_active" in column_names
    assert "created_at" in column_names
    assert "updated_at" in column_names

    # Verify foreign key on role_id referencing roles.id
    role_id_col = users_table.columns["role_id"]
    fk_targets = [list(fk.column.table.name for fk in role_id_col.foreign_keys)]
    assert ["roles"] in fk_targets or len(role_id_col.foreign_keys) > 0


def test_orm_model_instantiation_and_relationship():
    """Verify Python ORM instantiation of Role and User models."""
    admin_role = Role(id=1, name="ADMIN", description="Administrator")
    user = User(
        id=10,
        email="namisha@dealflow360.com",
        full_name="Namisha",
        hashed_password="hashed_secret_string",
        role_id=admin_role.id,
        role=admin_role,
        is_active=True,
    )

    assert user.email == "namisha@dealflow360.com"
    assert user.role.name == "ADMIN"
    assert repr(admin_role) == "<Role(id=1, name='ADMIN')>"
    assert "<User(id=10, email='namisha@dealflow360.com', role_id=1)>" in repr(user)


def test_user_read_schema_omits_hashed_password():
    """Verify UserRead Pydantic schema excludes sensitive hashed_password field."""
    # Ensure hashed_password is NOT exposed in schema fields
    assert "hashed_password" not in UserRead.model_fields

    now = datetime.now(timezone.utc)
    role_read = RoleRead(id=1, name="SALES_REP", description="Sales", created_at=now)
    user_read = UserRead(
        id=5,
        email="rudhra@dealflow360.com",
        full_name="Rudhrashini",
        role_id=1,
        is_active=True,
        created_at=now,
        updated_at=now,
        role=role_read,
    )

    data = user_read.model_dump()
    assert data["id"] == 5
    assert data["email"] == "rudhra@dealflow360.com"
    assert data["role"]["name"] == "SALES_REP"
    assert "hashed_password" not in data
