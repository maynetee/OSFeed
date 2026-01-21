"""Role-Based Access Control (RBAC) for OSFeed."""
from functools import wraps
from typing import List, Callable

from fastapi import HTTPException, status

from app.models.user import User, UserRole


# Permission definitions per role
ROLE_PERMISSIONS = {
    UserRole.ADMIN: ["*"],  # All permissions
    UserRole.ANALYST: [
        "channels:read",
        "channels:create",
        "channels:update",
        "messages:read",
        "messages:search",
        "digests:read",
        "digests:create",
        "export:csv",
        "export:pdf",
    ],
    UserRole.VIEWER: [
        "messages:read",
        "digests:read",
    ],
}


def has_permission(user: User, permission: str) -> bool:
    """Check if a user has a specific permission."""
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])

    # Admin has all permissions
    if "*" in user_permissions:
        return True

    return permission in user_permissions


def require_permission(permission: str):
    """Decorator to require a specific permission for an endpoint.

    Usage:
        @router.get("/channels")
        @require_permission("channels:read")
        async def list_channels(user: User = Depends(current_active_user)):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, user: User = None, **kwargs):
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if not has_permission(user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission} required",
                )

            return await func(*args, user=user, **kwargs)

        return wrapper

    return decorator


def require_role(allowed_roles: List[UserRole]):
    """Decorator to require specific roles for an endpoint.

    Usage:
        @router.delete("/channels/{id}")
        @require_role([UserRole.ADMIN, UserRole.ANALYST])
        async def delete_channel(id: UUID, user: User = Depends(current_active_user)):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, user: User = None, **kwargs):
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role {user.role.value} not authorized for this action",
                )

            return await func(*args, user=user, **kwargs)

        return wrapper

    return decorator
