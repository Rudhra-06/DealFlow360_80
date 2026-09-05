from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import create_access_token
from app.core.security import verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
)


class AuthenticationService:
    """Service orchestrating user credential verification and access token issuance."""

    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db
        self.user_repo: UserRepository = UserRepository()

    async def authenticate_user(self, email: str, plain_password: str) -> User:
        """Authenticates user credentials against the database.
        
        Performs email normalization, user lookup via UserRepository, bcrypt password verification,
        and active status check.
        
        Args:
            email: Candidate login email address.
            plain_password: Candidate plain-text password.

        Returns:
            Authenticated User ORM instance.

        Raises:
            InvalidCredentialsError: If user email does not exist or password verification fails.
            InactiveUserError: If user account is marked inactive.
        """
        if not email or not plain_password:
            raise InvalidCredentialsError("Invalid email or password.")

        normalized_email = email.strip().lower()
        user = await self.user_repo.get_by_email(self.db, normalized_email)

        if not user:
            raise InvalidCredentialsError("Invalid email or password.")

        if not verify_password(plain_password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password.")

        if not user.is_active:
            raise InactiveUserError("User account is inactive.")

        return user

    def create_user_access_token(self, user: User) -> str:
        """Generates a signed JWT access token for an authenticated User."""
        return create_access_token(subject=user.id)
