from app.core.jwt import ExpiredTokenError, InvalidTokenError, TokenError


class ServiceError(Exception):
    """Base domain exception for all Service Layer errors."""
    pass


class UserAlreadyExistsError(ServiceError):
    """Raised when attempting to create a user with an email that already exists."""
    pass


class RoleNotFoundError(ServiceError):
    """Raised when referencing a role ID that does not exist in the database."""
    pass


class AuthenticationError(ServiceError):
    """Base domain exception for authentication failures."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when email is unknown or candidate password fails verification.
    
    Protects against user enumeration by returning identical exception messages
    for both non-existent users and incorrect passwords.
    """
    pass


class InactiveUserError(AuthenticationError):
    """Raised when authenticating a user account marked inactive."""
    pass


__all__ = [
    "ServiceError",
    "UserAlreadyExistsError",
    "RoleNotFoundError",
    "AuthenticationError",
    "InvalidCredentialsError",
    "InactiveUserError",
    "TokenError",
    "InvalidTokenError",
    "ExpiredTokenError",
]


