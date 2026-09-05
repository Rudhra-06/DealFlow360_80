import sys
from pathlib import Path
import pytest
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Ensure backend root directory is in sys.path for test runs
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings


@pytest.fixture
async def db_session():
    """Provides a transactional AsyncSession using an outer connection transaction and savepoints.
    
    Even if Service Layer code invokes session.commit(), the commit operates on a nested SAVEPOINT.
    The outer connection transaction is rolled back upon test teardown, leaving zero persistent test records.
    """
    test_engine = create_async_engine(settings.async_database_url, poolclass=NullPool)
    async with test_engine.connect() as conn:
        trans = await conn.begin()
        async with AsyncSession(
            bind=conn,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        ) as session:
            try:
                yield session
            finally:
                await session.close()
        await trans.rollback()
    await test_engine.dispose()
