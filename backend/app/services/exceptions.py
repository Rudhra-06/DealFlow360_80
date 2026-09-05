class ServiceError(Exception):
    """Base domain exception for all Service Layer errors."""
    pass


class UserAlreadyExistsError(ServiceError):
    """Raised when attempting to create a user with an email that already exists."""
    pass


class RoleNotFoundError(ServiceError):
    """Raised when referencing a role ID that does not exist in the database."""
    pass
