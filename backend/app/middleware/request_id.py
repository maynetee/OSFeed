"""Request ID middleware — generates a unique ID per request and binds it to structlog context."""

import uuid
from contextvars import ContextVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Generate a UUID request ID, add it to structlog context and X-Request-ID response header."""

    async def dispatch(self, request: Request, call_next):
        rid = str(uuid.uuid4())
        request_id_var.set(rid)

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=rid)

        # Bind user_id if already set by auth middleware
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            structlog.contextvars.bind_contextvars(user_id=user_id)

        response = await call_next(request)

        # Bind user_id after call_next in case auth middleware set it during this request
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            structlog.contextvars.bind_contextvars(user_id=user_id)

        response.headers["X-Request-ID"] = rid
        return response
