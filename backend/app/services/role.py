from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.repositories.role import RoleRepository


class RoleService:
    """Service orchestrating business workflows and operations for Roles."""

    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db
        self.role_repo: RoleRepository = RoleRepository()

    async def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """Retrieves a Role by its primary key ID."""
        return await self.role_repo.get_by_id(self.db, role_id)

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Retrieves a Role by its unique name."""
        return await self.role_repo.get_by_name(self.db, name)

    async def list_roles(self) -> List[Role]:
        """Lists all roles."""
        return await self.role_repo.list_roles(self.db)
