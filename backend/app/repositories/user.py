from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserCreateInternal
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Async repository for User persistence operations."""

    def __init__(self) -> None:
        super().__init__(User)

    async def get_by_id(self, db: AsyncSession, user_id: int, load_role: bool = False) -> Optional[User]:
        """Fetch user by ID with optional eager loading of Role relationship."""
        stmt = select(User).where(User.id == user_id)
        if load_role:
            stmt = stmt.options(selectinload(User.role))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str, load_role: bool = False) -> Optional[User]:
        """Fetch user by unique email address with optional eager loading of Role relationship."""
        stmt = select(User).where(User.email == email)
        if load_role:
            stmt = stmt.options(selectinload(User.role))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users(
        self, db: AsyncSession, load_role: bool = False, limit: int = 100, offset: int = 0
    ) -> List[User]:
        """List users with pagination and optional eager loading of Role relationship."""
        stmt = select(User).order_by(User.id).offset(offset).limit(limit)
        if load_role:
            stmt = stmt.options(selectinload(User.role))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_users_by_role(
        self, db: AsyncSession, role_id: int, load_role: bool = False
    ) -> List[User]:
        """Fetch all users assigned to a specific role ID."""
        stmt = select(User).where(User.role_id == role_id).order_by(User.id)
        if load_role:
            stmt = stmt.options(selectinload(User.role))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create_user(self, db: AsyncSession, user_create: UserCreateInternal) -> User:
        """Instantiate and persist a new User record from internal creation schema.
        
        Flushes to session without committing so Service layer controls transaction boundaries.
        """
        user = User(
            email=user_create.email,
            full_name=user_create.full_name,
            hashed_password=user_create.hashed_password,
            role_id=user_create.role_id,
            is_active=user_create.is_active,
        )
        return await self.add(db, user)
