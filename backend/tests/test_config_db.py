import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, AsyncSessionLocal, get_db


def test_settings_load():
    """Verify application configuration settings load cleanly."""
    assert settings.APP_NAME == "DealFlow360 API"
    assert settings.API_V1_STR == "/api/v1"
    assert "postgresql+asyncpg://" in settings.async_database_url


def test_db_base_declarative():
    """Verify SQLAlchemy 2.x Base inherits from DeclarativeBase."""
    assert hasattr(Base, "metadata")


def test_session_engine_configuration():
    """Verify AsyncEngine and AsyncSessionLocal factory setup."""
    assert engine.url.drivername == "postgresql+asyncpg"
    assert AsyncSessionLocal is not None
