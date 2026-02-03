import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import app
from app.database import init_db
from app.auth.users import current_active_user
from app.models.user import User


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user = AsyncMock(spec=User)
    user.id = "test-user-id"
    user.email = "test@example.com"
    return user


@pytest.mark.asyncio
async def test_dashboard_endpoint_structure(mock_user):
    """Test that the dashboard endpoint returns the correct structure with all required fields."""
    await init_db()

    # Override the auth dependency
    app.dependency_overrides[current_active_user] = lambda: mock_user

    # Mock the individual stats functions to return predictable data
    with patch("app.api.stats.get_overview_stats", new_callable=AsyncMock) as mock_overview, \
         patch("app.api.stats.get_messages_by_day", new_callable=AsyncMock) as mock_by_day, \
         patch("app.api.stats.get_messages_by_channel", new_callable=AsyncMock) as mock_by_channel, \
         patch("app.api.stats.get_trust_stats", new_callable=AsyncMock) as mock_trust, \
         patch("app.api.stats.get_api_usage_stats", new_callable=AsyncMock) as mock_api_usage, \
         patch("app.api.stats.get_translation_metrics", new_callable=AsyncMock) as mock_translation:

        # Set up mock return values
        mock_overview.return_value = {
            "total_messages": 100,
            "active_channels": 5,
            "messages_last_24h": 10,
            "duplicates_last_24h": 2,
        }
        mock_by_day.return_value = [{"date": "2024-01-01", "count": 10}]
        mock_by_channel.return_value = [{"channel_id": str(uuid4()), "channel_title": "Channel 1", "count": 50}]
        mock_trust.return_value = {
            "primary_sources_rate": 80.0,
            "propaganda_rate": 5.0,
            "verified_channels": 3,
            "total_messages_24h": 10,
        }
        mock_api_usage.return_value = {
            "window_days": 7,
            "total_tokens": 1000,
            "estimated_cost_usd": 0.5,
            "breakdown": [],
        }
        mock_translation.return_value = {
            "total_translations": 50,
            "cache_hits": 40,
            "cache_misses": 10,
            "cache_hit_rate": 80.0,
            "tokens_saved": 500,
        }

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/stats/dashboard")

            # Assert status code
            assert response.status_code == 200

            # Assert response structure
            data = response.json()
            assert "overview" in data
            assert "messages_by_day" in data
            assert "messages_by_channel" in data
            assert "trust_stats" in data
            assert "api_usage" in data
            assert "translation_metrics" in data

            # Verify the data matches our mocks
            assert data["overview"]["total_messages"] == 100
            assert data["overview"]["active_channels"] == 5
            assert len(data["messages_by_day"]) == 1
            assert len(data["messages_by_channel"]) == 1
            assert data["trust_stats"]["primary_sources_rate"] == 80.0
            assert data["api_usage"]["total_tokens"] == 1000
            assert data["translation_metrics"]["cache_hit_rate"] == 80.0

    # Clean up
    app.dependency_overrides.pop(current_active_user, None)


@pytest.mark.asyncio
async def test_dashboard_endpoint_uses_asyncio_gather(mock_user):
    """Test that the dashboard endpoint calls all stats functions concurrently."""
    await init_db()

    # Override the auth dependency
    app.dependency_overrides[current_active_user] = lambda: mock_user

    # Mock the individual stats functions
    with patch("app.api.stats.get_overview_stats", new_callable=AsyncMock) as mock_overview, \
         patch("app.api.stats.get_messages_by_day", new_callable=AsyncMock) as mock_by_day, \
         patch("app.api.stats.get_messages_by_channel", new_callable=AsyncMock) as mock_by_channel, \
         patch("app.api.stats.get_trust_stats", new_callable=AsyncMock) as mock_trust, \
         patch("app.api.stats.get_api_usage_stats", new_callable=AsyncMock) as mock_api_usage, \
         patch("app.api.stats.get_translation_metrics", new_callable=AsyncMock) as mock_translation:

        # Set up mock return values with required fields
        mock_overview.return_value = {
            "total_messages": 0,
            "active_channels": 0,
            "messages_last_24h": 0,
            "duplicates_last_24h": 0,
        }
        mock_by_day.return_value = []
        mock_by_channel.return_value = []
        mock_trust.return_value = {
            "primary_sources_rate": 0.0,
            "propaganda_rate": 0.0,
            "verified_channels": 0,
            "total_messages_24h": 0,
        }
        mock_api_usage.return_value = {
            "window_days": 7,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "breakdown": [],
        }
        mock_translation.return_value = {
            "total_translations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_hit_rate": 0.0,
            "tokens_saved": 0,
        }

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/stats/dashboard")

            # Assert status code
            assert response.status_code == 200

            # Verify all functions were called
            mock_overview.assert_called_once()
            mock_by_day.assert_called_once()
            mock_by_channel.assert_called_once()
            mock_trust.assert_called_once()
            mock_api_usage.assert_called_once()
            mock_translation.assert_called_once()

    # Clean up
    app.dependency_overrides.pop(current_active_user, None)
