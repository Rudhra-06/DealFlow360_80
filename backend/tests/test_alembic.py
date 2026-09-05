import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.db.base import Base
from alembic.config import Config


def test_alembic_config_resolves_database_url():
    """Verify that Alembic configuration resolves async_database_url securely without hardcoded credentials in alembic.ini."""
    alembic_ini_path = backend_dir / "alembic.ini"
    assert alembic_ini_path.exists(), "alembic.ini must exist in backend directory"

    alembic_cfg = Config(str(alembic_ini_path))
    # Initially in alembic.ini, sqlalchemy.url is empty or un-configured
    ini_url = alembic_cfg.get_main_option("sqlalchemy.url")
    assert ini_url == "" or ini_url is None, "Database URL must not be hardcoded in alembic.ini"

    # Verify settings async_database_url is accessible and non-empty
    db_url = settings.async_database_url
    assert "postgresql+asyncpg://" in db_url


def test_alembic_target_metadata_binds_to_base():
    """Verify that Alembic env.py target_metadata matches app.db.base.Base.metadata."""
    import importlib.util
    from unittest.mock import MagicMock
    import alembic.context

    mock_cfg = MagicMock()
    mock_cfg.config_file_name = None
    alembic.context.config = mock_cfg
    alembic.context.is_offline_mode = MagicMock(return_value=True)
    alembic.context.configure = MagicMock()
    alembic.context.run_migrations = MagicMock()
    alembic.context.begin_transaction = MagicMock()

    env_path = backend_dir / "alembic" / "env.py"
    spec = importlib.util.spec_from_file_location("alembic_env", env_path)
    alembic_env = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(alembic_env)

    target_metadata = alembic_env.target_metadata

    assert target_metadata is Base.metadata
    # In Phase 1 - Part 3, target_metadata should currently have no business tables
    assert len(target_metadata.tables) == 0


def test_alembic_baseline_migration_exists():
    """Verify baseline migration script exists in alembic/versions/."""
    versions_dir = backend_dir / "alembic" / "versions"
    assert versions_dir.exists()
    baseline_files = list(versions_dir.glob("*_initial_schema_baseline.py"))
    assert len(baseline_files) == 1, "Baseline migration file must exist"
