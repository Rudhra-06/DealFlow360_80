from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.role import Role
from app.schemas.role import RoleCreateInternal
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """Async repository for Role persistence operations."""

    def __init__(self) -> None:
        super().__init__(Role)

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Role]:
        """Fetch a single Role record by unique name classification."""
        result = await db.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def list_roles(self, db: AsyncSession) -> List[Role]:
        """List all Role records ordered by ID."""
        result = await db.execute(select(Role).order_by(Role.id))
        return list(result.scalars().all())

    async def create_role(self, db: AsyncSession, role_create: RoleCreateInternal) -> Role:
        """Instantiate and persist a new Role record.
        
        Flushes to session without committing so Service layer controls transaction boundaries.
        """
        role = Role(
            name=role_create.name,
            description=role_create.description,
        )
        return await self.add(db, role)
