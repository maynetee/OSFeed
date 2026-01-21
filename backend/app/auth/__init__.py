"""Authentication package for OSFeed."""
from app.auth.users import (
    auth_backend,
    current_active_user,
    current_superuser,
    fastapi_users,
    get_user_manager,
)

__all__ = [
    "auth_backend",
    "current_active_user",
    "current_superuser",
    "fastapi_users",
    "get_user_manager",
]
