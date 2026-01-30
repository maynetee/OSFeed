"""Security headers middleware for adding HTTP security headers to all responses."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging

from app.config import get_settings

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
        self.settings = get_settings()
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

        # Check if security headers are enabled
        if not self.settings.security_headers_enabled:
            return response

        # Content-Security-Policy (if enabled)
        if self.settings.security_csp_enabled:
            response.headers["Content-Security-Policy"] = self.settings.security_csp_directives

        # X-Frame-Options
        response.headers["X-Frame-Options"] = self.settings.security_x_frame_options

        # X-Content-Type-Options (if enabled)
        if self.settings.security_x_content_type_options:
            response.headers["X-Content-Type-Options"] = "nosniff"

        # Strict-Transport-Security (if enabled)
        if self.settings.security_hsts_enabled:
            hsts_value = f"max-age={self.settings.security_hsts_max_age}"
            if self.settings.security_hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            response.headers["Strict-Transport-Security"] = hsts_value

        # Referrer-Policy
        response.headers["Referrer-Policy"] = self.settings.security_referrer_policy

        # Permissions-Policy
        response.headers["Permissions-Policy"] = self.settings.security_permissions_policy

        return response
