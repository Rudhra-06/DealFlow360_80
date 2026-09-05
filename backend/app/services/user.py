from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserCreateInternal
from app.services.exceptions import RoleNotFoundError, UserAlreadyExistsError


class UserService:
    """Service orchestrating business workflows and operations for User accounts."""

    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db
        self.user_repo: UserRepository = UserRepository()
        self.role_repo: RoleRepository = RoleRepository()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieves a User by primary key ID."""
        return await self.user_repo.get_by_id(self.db, user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieves a User by unique email address (email is normalized first)."""
        normalized_email = email.strip().lower()
        return await self.user_repo.get_by_email(self.db, normalized_email)

    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Lists users with pagination."""
        return await self.user_repo.list_users(self.db, limit=limit, offset=offset)

    async def create_user(
        self,
        email: str,
        full_name: str,
        plain_password: str,
        role_id: int,
    ) -> User:
        """Orchestrates user creation workflow.
        
        Performs email normalization, duplicate email validation, role existence validation,
        secure password hashing, repository addition/flushing, and transaction commitment.
        """
        # 1. Email Normalization
        normalized_email = email.strip().lower()

        # 2. Duplicate Email Check
        existing_user = await self.user_repo.get_by_email(self.db, normalized_email)
        if existing_user:
            raise UserAlreadyExistsError(f"User with email '{normalized_email}' already exists.")

        # 3. Role Validation
        role = await self.role_repo.get_by_id(self.db, role_id)
        if not role:
            raise RoleNotFoundError(f"Role with ID {role_id} not found.")

        # 4. Hash Password
        hashed_pwd = hash_password(plain_password)

        # 5. Build Internal Creation Schema
        user_in = UserCreateInternal(
            email=normalized_email,
            full_name=full_name,
            hashed_password=hashed_pwd,
            role_id=role_id,
            is_active=True,
        )

        # 6. Repository Persistence (adds to session and flushes)
        user = await self.user_repo.create_user(self.db, user_in)

        # 7. Transaction Ownership: Service Layer Commits
        try:
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception:
            await self.db.rollback()
            raise
