import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_docs_endpoint_disabled_in_production(monkeypatch):
    """Verify /docs endpoint returns 404 in production mode."""
    import importlib
    monkeypatch.setenv("APP_ENV", "production")

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
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_redoc_endpoint_disabled_in_production(monkeypatch):
    """Verify /redoc endpoint returns 404 in production mode."""
    import importlib
    monkeypatch.setenv("APP_ENV", "production")

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
        response = await client.get("/redoc")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_openapi_json_disabled_in_production(monkeypatch):
    """Verify /openapi.json endpoint returns 404 in production mode."""
    import importlib
    monkeypatch.setenv("APP_ENV", "production")

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
        response = await client.get("/openapi.json")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_docs_endpoint_enabled_in_development(monkeypatch):
    """Verify /docs endpoint is accessible in development mode."""
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


@pytest.mark.asyncio
async def test_redoc_endpoint_enabled_in_development(monkeypatch):
    """Verify /redoc endpoint is accessible in development mode."""
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
        response = await client.get("/redoc")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_openapi_json_enabled_in_development(monkeypatch):
    """Verify /openapi.json endpoint is accessible in development mode."""
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
        response = await client.get("/openapi.json")
        assert response.status_code == 200

        # Verify it's valid JSON and contains OpenAPI structure
        openapi_data = response.json()
        assert "openapi" in openapi_data
        assert "info" in openapi_data
        assert "paths" in openapi_data


@pytest.mark.asyncio
async def test_root_endpoint_minimal_in_production(monkeypatch):
    """Verify root endpoint returns minimal response in production mode."""
    import importlib
    monkeypatch.setenv("APP_ENV", "production")

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
        response = await client.get("/")
        assert response.status_code == 200

        data = response.json()
        # Should only contain status, not version or docs
        assert data == {"status": "ok"}
        assert "version" not in data
        assert "docs" not in data
        assert "message" not in data


@pytest.mark.asyncio
async def test_root_endpoint_detailed_in_development(monkeypatch):
    """Verify root endpoint returns detailed response in development mode."""
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
        response = await client.get("/")
        assert response.status_code == 200

        data = response.json()
        # Should contain message, version, and docs link
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert data["message"] == "OSFeed API"
        assert data["version"] == "0.1.0"
        assert data["docs"] == "/docs"


@pytest.mark.asyncio
async def test_production_mode_blocks_api_introspection():
    """Verify that production mode prevents API schema introspection."""
    import importlib
    import os

    # Set production mode
    os.environ["APP_ENV"] = "production"

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
        # All documentation endpoints should return 404
        docs_response = await client.get("/docs")
        redoc_response = await client.get("/redoc")
        openapi_response = await client.get("/openapi.json")

        assert docs_response.status_code == 404
        assert redoc_response.status_code == 404
        assert openapi_response.status_code == 404

        # Root endpoint should not reveal version info
        root_response = await client.get("/")
        root_data = root_response.json()
        assert "version" not in root_data
        assert "docs" not in root_data


@pytest.mark.asyncio
async def test_development_mode_allows_full_api_access():
    """Verify that development mode provides full API documentation access."""
    import importlib
    import os

    # Set development mode
    os.environ["APP_ENV"] = "development"

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
        # All documentation endpoints should be accessible
        docs_response = await client.get("/docs")
        redoc_response = await client.get("/redoc")
        openapi_response = await client.get("/openapi.json")

        assert docs_response.status_code == 200
        assert redoc_response.status_code == 200
        assert openapi_response.status_code == 200

        # Root endpoint should reveal API information
        root_response = await client.get("/")
        root_data = root_response.json()
        assert "version" in root_data
        assert "docs" in root_data
        assert "message" in root_data
