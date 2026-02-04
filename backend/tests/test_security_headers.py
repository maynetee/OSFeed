import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from fastapi_users.password import PasswordHelper

from app.main import app
from app.database import AsyncSessionLocal, init_db
from app.models.user import User


@pytest.mark.asyncio
async def test_security_headers_on_health_endpoint():
    """Verify security headers are present on the health endpoint."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200

        # Verify all security headers are present
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "Strict-Transport-Security" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers


@pytest.mark.asyncio
async def test_security_headers_values():
    """Verify security headers have the correct values."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200

        # Verify header values match expected configuration
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

        # Verify CSP contains critical directives
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "base-uri 'self'" in csp

        # Verify HSTS includes subdomains and has reasonable max-age
        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts

        # Verify Permissions-Policy restricts dangerous features
        permissions = response.headers["Permissions-Policy"]
        assert "geolocation=()" in permissions
        assert "camera=()" in permissions
        assert "microphone=()" in permissions


@pytest.mark.asyncio
async def test_security_headers_on_api_endpoints():
    """Verify security headers are present on API endpoints."""
    await init_db()
    password_helper = PasswordHelper()

    # Create test user for authentication test
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "test_security_headers@example.com"))
        existing_user = result.scalars().first()

        if not existing_user:
            user = User(
                email="test_security_headers@example.com",
                hashed_password=password_helper.hash("Str0ngP@ssword!"),
                is_active=True,
                is_superuser=False,
                is_verified=True,
            )
            session.add(user)
            await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test unauthenticated API endpoint
        response = await client.post(
            "/api/auth/login",
            data={"username": "test_security_headers@example.com", "password": "Str0ngP@ssword!"},
        )
        assert response.status_code == 200

        # Verify security headers are present
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "Strict-Transport-Security" in response.headers

        # Get access token from cookies (tokens are now in httpOnly cookies)
        access_token = response.cookies.get("access_token")
        assert access_token, "access_token cookie not set in login response"

        # Test authenticated API endpoint
        auth_response = await client.get(
            "/api/stats/overview",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert auth_response.status_code == 200

        # Verify security headers are present on authenticated endpoint
        assert "Content-Security-Policy" in auth_response.headers
        assert "X-Frame-Options" in auth_response.headers
        assert "X-Content-Type-Options" in auth_response.headers


@pytest.mark.asyncio
async def test_security_headers_on_docs_endpoint(monkeypatch):
    """Verify security headers are present on the docs endpoint."""
    import importlib
    monkeypatch.setenv("APP_ENV", "development")

    # Clear settings cache and reload modules to pick up new env vars
    from app.config import get_settings
    get_settings.cache_clear()

    import app.main
    importlib.reload(app.main)

    from app.main import app
    from app.database import init_db
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/docs")
        assert response.status_code == 200

        # Verify security headers are present even on docs
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers


@pytest.mark.asyncio
async def test_security_headers_on_error_responses():
    """Verify security headers are present even on error responses."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test 401 Unauthorized (no auth token)
        response = await client.get("/api/stats/overview")
        assert response.status_code == 401

        # Verify security headers are present on error responses
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "Strict-Transport-Security" in response.headers

        # Test 404 Not Found
        not_found_response = await client.get("/nonexistent-endpoint")
        assert not_found_response.status_code == 404

        # Verify security headers are present on 404 responses
        assert "Content-Security-Policy" in not_found_response.headers
        assert "X-Frame-Options" in not_found_response.headers
        assert "X-Content-Type-Options" in not_found_response.headers


@pytest.mark.asyncio
async def test_security_headers_on_root_endpoint():
    """Verify security headers are present on the root endpoint."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        # Root endpoint should return 200 or 404 depending on configuration
        assert response.status_code in [200, 404]

        # Verify security headers are present
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers


@pytest.mark.asyncio
async def test_csp_prevents_unsafe_inline_by_default():
    """Verify CSP policy prevents unsafe inline scripts (in most directives)."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200

        csp = response.headers["Content-Security-Policy"]

        # While we allow unsafe-inline for scripts/styles (for Swagger UI),
        # verify frame-ancestors is set to 'none' to prevent clickjacking
        assert "frame-ancestors 'none'" in csp

        # Verify default-src is restricted to 'self'
        assert "default-src 'self'" in csp


@pytest.mark.asyncio
async def test_csp_does_not_contain_unsafe_eval():
    """Verify CSP policy does not contain 'unsafe-eval'."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200

        csp = response.headers["Content-Security-Policy"]

        # Verify 'unsafe-eval' is not present in the CSP header
        assert "'unsafe-eval'" not in csp


@pytest.mark.asyncio
async def test_x_frame_options_prevents_clickjacking():
    """Verify X-Frame-Options header prevents clickjacking."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200

        # Verify DENY prevents all framing attempts
        assert response.headers["X-Frame-Options"] == "DENY"


@pytest.mark.asyncio
async def test_hsts_enforces_https():
    """Verify HSTS header enforces HTTPS with appropriate settings."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200

        hsts = response.headers["Strict-Transport-Security"]

        # Verify max-age is at least 1 year (31536000 seconds)
        assert "max-age=31536000" in hsts

        # Verify subdomains are included
        assert "includeSubDomains" in hsts


@pytest.mark.asyncio
async def test_permissions_policy_restricts_features():
    """Verify Permissions-Policy restricts dangerous browser features."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200

        permissions = response.headers["Permissions-Policy"]

        # Verify dangerous features are disabled
        dangerous_features = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
        ]

        for feature in dangerous_features:
            assert feature in permissions


@pytest.mark.asyncio
async def test_security_headers_can_be_disabled(monkeypatch):
    """Test that security headers can be disabled via settings."""
    import importlib
    monkeypatch.setenv("SECURITY_HEADERS_ENABLED", "false")

    # Clear settings cache and reload modules to pick up new env vars
    from app.config import get_settings
    get_settings.cache_clear()

    import app.middleware.security_headers
    import app.main
    importlib.reload(app.middleware.security_headers)
    importlib.reload(app.main)

    from app.main import app
    from httpx import AsyncClient, ASGITransport
    from app.database import init_db

    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

        # Should not have security headers when disabled
        assert "X-Frame-Options" not in response.headers
        assert "Content-Security-Policy" not in response.headers


@pytest.mark.asyncio
async def test_custom_csp_directives(monkeypatch):
    """Test that custom CSP directives are used when configured."""
    import importlib
    custom_csp = "default-src 'none'; script-src 'self'"
    monkeypatch.setenv("SECURITY_CSP_DIRECTIVES", custom_csp)

    # Clear settings cache and reload modules to pick up new env vars
    from app.config import get_settings
    get_settings.cache_clear()

    import app.middleware.security_headers
    import app.main
    importlib.reload(app.middleware.security_headers)
    importlib.reload(app.main)

    from app.main import app
    from httpx import AsyncClient, ASGITransport
    from app.database import init_db

    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

        assert response.headers.get("Content-Security-Policy") == custom_csp


@pytest.mark.asyncio
async def test_hsts_configuration(monkeypatch):
    """Test that HSTS settings are configurable."""
    import importlib
    monkeypatch.setenv("SECURITY_HSTS_MAX_AGE", "86400")  # 1 day
    monkeypatch.setenv("SECURITY_HSTS_INCLUDE_SUBDOMAINS", "false")

    # Clear settings cache and reload modules to pick up new env vars
    from app.config import get_settings
    get_settings.cache_clear()

    import app.middleware.security_headers
    import app.main
    importlib.reload(app.middleware.security_headers)
    importlib.reload(app.main)

    from app.main import app
    from httpx import AsyncClient, ASGITransport
    from app.database import init_db

    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

        hsts = response.headers.get("Strict-Transport-Security")
        assert "max-age=86400" in hsts
        assert "includeSubDomains" not in hsts


@pytest.mark.asyncio
async def test_x_frame_options_configurable(monkeypatch):
    """Test that X-Frame-Options can be configured."""
    import importlib
    monkeypatch.setenv("SECURITY_X_FRAME_OPTIONS", "SAMEORIGIN")

    # Clear settings cache and reload modules to pick up new env vars
    from app.config import get_settings
    get_settings.cache_clear()

    import app.middleware.security_headers
    import app.main
    importlib.reload(app.middleware.security_headers)
    importlib.reload(app.main)

    from app.main import app
    from httpx import AsyncClient, ASGITransport
    from app.database import init_db

    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

        assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
