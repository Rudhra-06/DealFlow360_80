from typing import Callable, Sequence

from fastapi import Depends, HTTPException, status

from app.api.dependencies.auth import get_current_user
from app.models.user import User


def require_roles(*allowed_roles: str) -> Callable[..., User]:
    """Dependency factory enforcing Role-Based Access Control (RBAC).

    Requires that the authenticated user returned by `get_current_user` possesses
    at least one of the specified allowed roles. Role information is read directly
    from the current database state attached to `user.role`.

    Raises:
        HTTPException 403 Forbidden if user role is missing or not allowed.
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not current_user.role or current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker
