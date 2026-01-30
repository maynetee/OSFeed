"""Security headers middleware for adding HTTP security headers to all responses."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all HTTP responses.

    Headers added:
    - Content-Security-Policy: Protects against XSS attacks
    - X-Frame-Options: Prevents clickjacking
    - X-Content-Type-Options: Prevents MIME-sniffing
    - Strict-Transport-Security: Enforces HTTPS
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    """

    def __init__(self, app, **options):
        """
        Initialize the security headers middleware.

        Args:
            app: The FastAPI application
            **options: Optional configuration (for future extensibility)
        """
        super().__init__(app)
        self.options = options
        logger.info("Security headers middleware initialized")

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request and add security headers to the response.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            Response with security headers added
        """
        response = await call_next(request)

        # Content Security Policy - Restrictive policy for API
        # For API endpoints, we want to prevent any content execution
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Prevent clickjacking - don't allow framing
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enforce HTTPS (max-age: 1 year)
        # Note: Only applies when accessed via HTTPS
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        # Control referrer information - send origin only for cross-origin
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy - disable potentially dangerous features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        return response
