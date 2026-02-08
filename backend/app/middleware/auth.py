"""Global authentication middleware that enforces JWT auth on all routes by default."""

import logging

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings

logger = logging.getLogger(__name__)

# Routes that do not require authentication (prefix matching)
PUBLIC_ROUTES: list[str] = [
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",
    "/api/auth/verify",
    "/api/auth/request-verify-token",
    "/api/auth/forgot-password",
    "/api/auth/reset-password",
    "/api/stripe/webhook",
    "/api/contact-sales",
    "/api/newsletter",
    "/api/collections/curated",
]


def _is_public(path: str) -> bool:
    """Check if a request path matches any public route (exact or prefix)."""
    for route in PUBLIC_ROUTES:
        if route == "/":
            if path == "/":
                return True
        elif path == route or path.startswith(route + "/"):
            return True
    return False


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that rejects unauthenticated requests to non-public routes."""

    def __init__(self, app, **options):
        super().__init__(app)
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next):
        # Always allow CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # Allow public routes
        if _is_public(request.url.path):
            return await call_next(request)

        # Skip middleware when auth dependency is overridden (test environment).
        # Tests use app.dependency_overrides[current_active_user] to inject a
        # fake user — the per-route Depends() handles auth in that case.
        from app.auth.users import current_active_user  # noqa: E402

        if current_active_user in request.app.dependency_overrides:
            return await call_next(request)

        # Extract JWT from cookie
        token = request.cookies.get(self.settings.cookie_access_token_name)
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"},
            )

        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm],
                audience=["fastapi-users:auth"],
            )
            user_id = payload.get("sub")
            if user_id is None:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Not authenticated"},
                )
            request.state.user_id = user_id
        except (jwt.PyJWTError, Exception):
            return JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"},
            )

        return await call_next(request)
