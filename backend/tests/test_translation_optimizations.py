from datetime import datetime, timedelta, timezone

import pytest

from app.services.llm_translator import LLMTranslator


def test_translation_priority_skips_trivial_patterns():
    translator = LLMTranslator()
    assert translator.get_translation_priority("https://example.com", source_lang="en") == "skip"
    assert translator.get_translation_priority("#hashtag", source_lang="en") == "skip"
    assert translator.get_translation_priority("@mention", source_lang="en") == "skip"
    assert translator.get_translation_priority("12345", source_lang="en") == "skip"
    assert translator.get_translation_priority("!!!", source_lang="en") == "skip"


def test_translation_priority_same_language_skip():
    translator = LLMTranslator()
    assert (
        translator.get_translation_priority(
            "bonjour",
            source_lang="fr",
            target_lang="fr",
            published_at=datetime.now(timezone.utc),
        )
        == "skip"
    )


def test_translation_priority_by_age():
    translator = LLMTranslator()
    now = datetime.now(timezone.utc)
    assert (
        translator.get_translation_priority(
            "message",
            source_lang="fr",
            target_lang="en",
            published_at=now - timedelta(hours=2),
        )
        == "high"
    )
    assert (
        translator.get_translation_priority(
            "message",
            source_lang="fr",
            target_lang="en",
            published_at=now - timedelta(days=2),
        )
        == "normal"
    )
    assert (
        translator.get_translation_priority(
            "message",
            source_lang="fr",
            target_lang="en",
            published_at=now - timedelta(days=10),
        )
        == "low"
    )


def test_model_routing_fallback_to_google_when_keys_missing():
    translator = LLMTranslator()
    translator.api_key = ""
    translator.gemini_api_key = ""
    provider, model = translator._resolve_model("gemini-flash")
    assert provider == "google"
    assert model == "google"


@pytest.mark.asyncio
async def test_translate_skips_trivial_text_without_api_call():
    translator = LLMTranslator()
    translated, lang, priority = await translator.translate("https://example.com")
    assert translated == "https://example.com"
    assert lang == "unknown"
    assert priority == "skip"
