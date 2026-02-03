import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.cache_service import CacheService, get_cache_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_settings(**overrides):
    """Create mock settings with given overrides."""
    defaults = dict(redis_url="redis://localhost:6379/0")
    defaults.update(overrides)
    return MagicMock(**defaults)


# ---------------------------------------------------------------------------
# CacheService – graceful degradation when Redis disabled
# ---------------------------------------------------------------------------


class TestCacheServiceDisabled:
    @pytest.mark.asyncio
    async def test_get_returns_none_when_redis_disabled(self):
        with patch("app.services.cache_service.get_settings") as mock_settings:
            mock_settings.return_value = _make_settings(redis_url="")
            service = CacheService()
            result = await service.get("test_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_set_returns_false_when_redis_disabled(self):
        with patch("app.services.cache_service.get_settings") as mock_settings:
            mock_settings.return_value = _make_settings(redis_url="")
            service = CacheService()
            result = await service.set("test_key", "test_value")
            assert result is False

    @pytest.mark.asyncio
    async def test_setex_returns_false_when_redis_disabled(self):
        with patch("app.services.cache_service.get_settings") as mock_settings:
            mock_settings.return_value = _make_settings(redis_url="")
            service = CacheService()
            result = await service.setex("test_key", 60, "test_value")
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_redis_disabled(self):
        with patch("app.services.cache_service.get_settings") as mock_settings:
            mock_settings.return_value = _make_settings(redis_url="")
            service = CacheService()
            result = await service.delete("test_key")
            assert result is False

    @pytest.mark.asyncio
    async def test_incr_returns_zero_when_redis_disabled(self):
        with patch("app.services.cache_service.get_settings") as mock_settings:
            mock_settings.return_value = _make_settings(redis_url="")
            service = CacheService()
            result = await service.incr("test_key")
            assert result == 0


# ---------------------------------------------------------------------------
# CacheService – successful operations with mocked Redis
# ---------------------------------------------------------------------------


class TestCacheServiceWithMockedRedis:
    @pytest.mark.asyncio
    async def test_get_returns_cached_value(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "cached_value"

        with patch("app.services.cache_service.get_settings", return_value=_make_settings()):
            service = CacheService()
            service._redis = mock_redis
            result = await service.get("test_key")

        assert result == "cached_value"
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_returns_none_when_key_not_found(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with patch("app.services.cache_service.get_settings", return_value=_make_settings()):
            service = CacheService()
            service._redis = mock_redis
            result = await service.get("nonexistent_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_stores_value_successfully(self):
        mock_redis = AsyncMock()

        with patch("app.services.cache_service.get_settings", return_value=_make_settings()):
            service = CacheService()
            service._redis = mock_redis
            result = await service.set("test_key", "test_value")

        assert result is True
        mock_redis.set.assert_called_once_with("test_key", "test_value")

    @pytest.mark.asyncio
    async def test_setex_stores_value_with_ttl(self):
        mock_redis = AsyncMock()

        with patch("app.services.cache_service.get_settings", return_value=_make_settings()):
            service = CacheService()
            service._redis = mock_redis
            result = await service.setex("test_key", 300, "test_value")

        assert result is True
        mock_redis.setex.assert_called_once_with("test_key", 300, "test_value")

    @pytest.mark.asyncio
    async def test_delete_removes_key_successfully(self):
        mock_redis = AsyncMock()

        with patch("app.services.cache_service.get_settings", return_value=_make_settings()):
            service = CacheService()
            service._redis = mock_redis
            result = await service.delete("test_key")

        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_incr_increments_counter(self):
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 5

        with patch("app.services.cache_service.get_settings", return_value=_make_settings()):
            service = CacheService()
            service._redis = mock_redis
            result = await service.incr("counter_key")

        assert result == 5
        mock_redis.incr.assert_called_once_with("counter_key")


# ---------------------------------------------------------------------------
# CacheService – error handling
# ---------------------------------------------------------------------------


class TestCacheServiceErrorHandling:
    @pytest.mark.asyncio
    async def test_get_returns_none_on_redis_error(self):
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Redis connection failed")

        with patch("app.services.cache_service.get_settings", return_value=_make_settings()):
            service = CacheService()
            service._redis = mock_redis
            result = await service.get("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_returns_false_on_redis_error(self):
        mock_redis = AsyncMock()
        mock_redis.set.side_effect = Exception("Redis connection failed")

        with patch("app.services.cache_service.get_settings", return_value=_make_settings()):
            service = CacheService()
            service._redis = mock_redis
            result = await service.set("test_key", "test_value")

        assert result is False

    @pytest.mark.asyncio
    async def test_setex_returns_false_on_redis_error(self):
        mock_redis = AsyncMock()
        mock_redis.setex.side_effect = Exception("Redis connection failed")

        with patch("app.services.cache_service.get_settings", return_value=_make_settings()):
            service = CacheService()
            service._redis = mock_redis
            result = await service.setex("test_key", 60, "test_value")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_returns_false_on_redis_error(self):
        mock_redis = AsyncMock()
        mock_redis.delete.side_effect = Exception("Redis connection failed")

        with patch("app.services.cache_service.get_settings", return_value=_make_settings()):
            service = CacheService()
            service._redis = mock_redis
            result = await service.delete("test_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_incr_returns_zero_on_redis_error(self):
        mock_redis = AsyncMock()
        mock_redis.incr.side_effect = Exception("Redis connection failed")

        with patch("app.services.cache_service.get_settings", return_value=_make_settings()):
            service = CacheService()
            service._redis = mock_redis
            result = await service.incr("counter_key")

        assert result == 0


# ---------------------------------------------------------------------------
# CacheService – Redis connection management
# ---------------------------------------------------------------------------


class TestCacheServiceConnectionManagement:
    @pytest.mark.asyncio
    async def test_get_redis_creates_connection_once(self):
        with patch("app.services.cache_service.get_settings", return_value=_make_settings()):
            with patch("app.services.cache_service.Redis") as mock_redis_class:
                mock_redis_instance = AsyncMock()
                mock_redis_class.from_url.return_value = mock_redis_instance

                service = CacheService()

                # Call twice
                redis1 = await service._get_redis()
                redis2 = await service._get_redis()

                # Should return same instance
                assert redis1 is redis2
                # Should only create connection once
                mock_redis_class.from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_closes_redis_connection(self):
        mock_redis = AsyncMock()

        with patch("app.services.cache_service.get_settings", return_value=_make_settings()):
            service = CacheService()
            service._redis = mock_redis
            await service.close()

        mock_redis.close.assert_called_once()
        assert service._redis is None

    @pytest.mark.asyncio
    async def test_close_does_nothing_when_no_connection(self):
        with patch("app.services.cache_service.get_settings", return_value=_make_settings()):
            service = CacheService()
            # Should not raise an error
            await service.close()


# ---------------------------------------------------------------------------
# Singleton pattern
# ---------------------------------------------------------------------------


class TestCacheServiceSingleton:
    def test_get_cache_service_returns_same_instance(self):
        # Reset singleton
        import app.services.cache_service as cache_module
        cache_module._cache_service = None

        service1 = get_cache_service()
        service2 = get_cache_service()

        assert service1 is service2

    def test_get_cache_service_creates_cache_service_instance(self):
        # Reset singleton
        import app.services.cache_service as cache_module
        cache_module._cache_service = None

        service = get_cache_service()

        assert isinstance(service, CacheService)
