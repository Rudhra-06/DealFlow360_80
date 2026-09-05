from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async repository providing standard persistence operations for SQLAlchemy models."""

    def __init__(self, model: Type[ModelType]) -> None:
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Fetch a single record by primary key."""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def list(self, db: AsyncSession, limit: int = 100, offset: int = 0) -> List[ModelType]:
        """List records with pagination support."""
        result = await db.execute(select(self.model).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def add(self, db: AsyncSession, obj: ModelType) -> ModelType:
        """Add an ORM instance to session and flush pending changes.
        
        Note: Transaction ownership remains with the caller/Service layer.
        This method calls flush() to obtain database-generated IDs/defaults without committing.
        """
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def delete(self, db: AsyncSession, obj: ModelType) -> None:
        """Delete an ORM instance from session and flush pending changes."""
        await db.delete(obj)
        await db.flush()
