import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from app.main import app
from app.database import init_db


@pytest.mark.asyncio
async def test_health_check_success():
    """Test health check returns healthy status when database is connected."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "error" not in data


@pytest.mark.asyncio
async def test_health_check_database_failure_no_error_details():
    """Test health check does not expose error details when database connection fails."""
    await init_db()

    # Mock database connection to raise an exception
    with patch("app.main.get_engine") as mock_get_engine:
        mock_engine = AsyncMock()
        mock_connect = AsyncMock()
        mock_connect.__aenter__.side_effect = Exception("Connection refused: database error details")
        mock_engine.connect.return_value = mock_connect
        mock_get_engine.return_value = mock_engine

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

            # Assert 503 status code
            assert response.status_code == 503

            # Assert response structure
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database"] == "disconnected"

            # Assert 'error' field is NOT present in response
            assert "error" not in data, "Response should not contain 'error' field with exception details"


@pytest.mark.asyncio
async def test_health_check_query_execution_failure():
    """Test health check handles query execution failures without exposing details."""
    await init_db()

    # Mock database query to raise an exception
    with patch("app.main.get_engine") as mock_get_engine:
        mock_engine = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("SQL error: invalid query syntax")
        mock_connect = AsyncMock()
        mock_connect.__aenter__.return_value = mock_conn
        mock_engine.connect.return_value = mock_connect
        mock_get_engine.return_value = mock_engine

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

            # Assert 503 status code
            assert response.status_code == 503

            # Assert response structure
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database"] == "disconnected"

            # Assert 'error' field is NOT present
            assert "error" not in data, "Response should not expose internal error messages"

            # Assert only expected fields are present
            assert set(data.keys()) == {"status", "database"}, "Response should only contain status and database fields"
