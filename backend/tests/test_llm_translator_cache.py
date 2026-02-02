import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.llm_translator import LLMTranslator
import app.services.llm_translator as translator_mod


@pytest.fixture
def translator_no_redis(monkeypatch):
    """Create a translator with Redis disabled to test in-memory cache."""
    monkeypatch.setenv("REDIS_URL", "")
    translator = LLMTranslator()
    translator._redis = None  # Ensure Redis is disabled
    return translator


@pytest.mark.asyncio
async def test_cache_evicts_oldest_entry(translator_no_redis, monkeypatch):
    """Test that cache evicts the oldest entry when max size is reached."""
    # Set a small cache size for testing
    monkeypatch.setattr(translator_mod.settings, "translation_memory_cache_max_size", 3)

    translator = translator_no_redis

    # Mock the actual translation to avoid API calls
    async def mock_translate_llm(text, source_lang, target_lang, model):
        return f"translated_{text}"

    monkeypatch.setattr(translator, "_translate_with_llm", mock_translate_llm)
    monkeypatch.setattr(translator, "detect_language", AsyncMock(return_value="fr"))

    # Add 3 entries to fill the cache
    await translator.translate("text1", source_lang="fr", target_lang="en")
    await translator.translate("text2", source_lang="fr", target_lang="en")
    await translator.translate("text3", source_lang="fr", target_lang="en")

    assert len(translator.cache) == 3

    # Verify the cache keys
    key1 = translator._cache_key("text1", "fr", "en")
    key2 = translator._cache_key("text2", "fr", "en")
    key3 = translator._cache_key("text3", "fr", "en")

    assert key1 in translator.cache
    assert key2 in translator.cache
    assert key3 in translator.cache

    # Add a 4th entry - should evict the oldest (key1)
    await translator.translate("text4", source_lang="fr", target_lang="en")

    assert len(translator.cache) == 3
    assert key1 not in translator.cache  # Oldest entry evicted
    assert key2 in translator.cache
    assert key3 in translator.cache
    key4 = translator._cache_key("text4", "fr", "en")
    assert key4 in translator.cache


@pytest.mark.asyncio
async def test_cache_lru_order(translator_no_redis, monkeypatch):
    """Test that accessing a cached entry moves it to the end (most recently used)."""
    # Set a small cache size for testing
    monkeypatch.setattr(translator_mod.settings, "translation_memory_cache_max_size", 3)

    translator = translator_no_redis

    # Mock the actual translation
    async def mock_translate_llm(text, source_lang, target_lang, model):
        return f"translated_{text}"

    monkeypatch.setattr(translator, "_translate_with_llm", mock_translate_llm)
    monkeypatch.setattr(translator, "detect_language", AsyncMock(return_value="fr"))

    # Add 3 entries
    await translator.translate("text1", source_lang="fr", target_lang="en")
    await translator.translate("text2", source_lang="fr", target_lang="en")
    await translator.translate("text3", source_lang="fr", target_lang="en")

    key1 = translator._cache_key("text1", "fr", "en")
    key2 = translator._cache_key("text2", "fr", "en")
    key3 = translator._cache_key("text3", "fr", "en")

    # Access text1 (the oldest) - should move it to the end
    result = await translator.translate("text1", source_lang="fr", target_lang="en")
    assert result[0] == "translated_text1"  # Verify cache hit

    # Now add text4 - should evict text2 (now the oldest), not text1
    await translator.translate("text4", source_lang="fr", target_lang="en")

    assert len(translator.cache) == 3
    assert key1 in translator.cache  # text1 should still be there (was accessed)
    assert key2 not in translator.cache  # text2 should be evicted (oldest)
    assert key3 in translator.cache
    key4 = translator._cache_key("text4", "fr", "en")
    assert key4 in translator.cache


@pytest.mark.asyncio
async def test_cache_respects_max_size(translator_no_redis, monkeypatch):
    """Test that cache size never exceeds the configured maximum."""
    # Set a small cache size for testing
    max_size = 5
    monkeypatch.setattr(translator_mod.settings, "translation_memory_cache_max_size", max_size)

    translator = translator_no_redis

    # Mock the actual translation
    async def mock_translate_llm(text, source_lang, target_lang, model):
        return f"translated_{text}"

    monkeypatch.setattr(translator, "_translate_with_llm", mock_translate_llm)
    monkeypatch.setattr(translator, "detect_language", AsyncMock(return_value="fr"))

    # Add more than max_size entries
    for i in range(max_size * 2):
        await translator.translate(f"text{i}", source_lang="fr", target_lang="en")
        # Cache size should never exceed max_size
        assert len(translator.cache) <= max_size

    # Final verification
    assert len(translator.cache) == max_size


@pytest.mark.asyncio
async def test_cache_hit_count_increments(translator_no_redis, monkeypatch):
    """Test that cache hit count increments when entries are accessed."""
    monkeypatch.setattr(translator_mod.settings, "translation_memory_cache_max_size", 10)

    translator = translator_no_redis

    # Mock the actual translation
    async def mock_translate_llm(text, source_lang, target_lang, model):
        return f"translated_{text}"

    monkeypatch.setattr(translator, "_translate_with_llm", mock_translate_llm)
    monkeypatch.setattr(translator, "detect_language", AsyncMock(return_value="fr"))

    # First translation - cache miss, hit count = 1
    await translator.translate("hello", source_lang="fr", target_lang="en")

    cache_key = translator._cache_key("hello", "fr", "en")
    cached_value, hit_count = translator.cache[cache_key]
    assert cached_value == "translated_hello"
    assert hit_count == 1

    # Second translation - cache hit, hit count should increment
    await translator.translate("hello", source_lang="fr", target_lang="en")
    cached_value, hit_count = translator.cache[cache_key]
    assert hit_count == 2

    # Third translation - another cache hit
    await translator.translate("hello", source_lang="fr", target_lang="en")
    cached_value, hit_count = translator.cache[cache_key]
    assert hit_count == 3


@pytest.mark.asyncio
async def test_cache_works_independently_per_language_pair(translator_no_redis, monkeypatch):
    """Test that same text with different language pairs creates separate cache entries."""
    monkeypatch.setattr(translator_mod.settings, "translation_memory_cache_max_size", 10)

    translator = translator_no_redis

    # Mock the actual translation
    async def mock_translate_llm(text, source_lang, target_lang, model):
        return f"{source_lang}_{target_lang}_{text}"

    monkeypatch.setattr(translator, "_translate_with_llm", mock_translate_llm)

    # Same text, different language pairs
    result1 = await translator.translate("hello", source_lang="fr", target_lang="en")
    result2 = await translator.translate("hello", source_lang="es", target_lang="en")
    result3 = await translator.translate("hello", source_lang="fr", target_lang="de")

    # Should have 3 separate cache entries
    assert len(translator.cache) == 3

    # Verify each translation is cached separately
    assert result1[0] == "fr_en_hello"
    assert result2[0] == "es_en_hello"
    assert result3[0] == "fr_de_hello"
