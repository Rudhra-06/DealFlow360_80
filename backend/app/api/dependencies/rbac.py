from typing import Any, Callable, Sequence

from fastapi import Depends, HTTPException, status

from app.api.dependencies.auth import get_current_user
from app.models.user import User


def require_roles(*allowed_roles: Any) -> Callable[..., User]:
    """Dependency factory enforcing Role-Based Access Control (RBAC).

    Requires that the authenticated user returned by `get_current_user` possesses
    at least one of the specified allowed roles. Role information is read directly
    from the current database state attached to `user.role`.

    Raises:
        HTTPException 403 Forbidden if user role is missing or not allowed.
    """
    allowed_set = {r.value if hasattr(r, "value") else str(r) for r in allowed_roles}

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_role = current_user.role.name if current_user.role else None
        if not user_role or user_role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker

