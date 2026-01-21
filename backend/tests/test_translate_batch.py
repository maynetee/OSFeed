import pytest

from app.services.llm_translator import BATCH_SEPARATOR, LLMTranslator


class _FakeUsage:
    prompt_tokens = 5
    completion_tokens = 7


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeChoice(content)]
        self.usage = _FakeUsage()


class _FakeCompletions:
    def __init__(self, content: str) -> None:
        self._content = content

    async def create(self, *args, **kwargs) -> _FakeResponse:
        return _FakeResponse(self._content)


class _FakeChat:
    def __init__(self, content: str) -> None:
        self.completions = _FakeCompletions(content)


class _FakeClient:
    def __init__(self, content: str) -> None:
        self.chat = _FakeChat(content)


@pytest.mark.asyncio
async def test_translate_batch_llm_splits_by_separator() -> None:
    translator = LLMTranslator()
    combined = f"hello{BATCH_SEPARATOR}bye"
    translator._client = _FakeClient(combined)

    results = await translator._translate_batch_llm(["hola", "adios"], "es", "en", model="gpt-4o-mini")

    assert results == ["hello", "bye"]


@pytest.mark.asyncio
async def test_translate_batch_llm_fallback_on_mismatch(monkeypatch) -> None:
    translator = LLMTranslator()
    translator._client = _FakeClient("single output")
    
    # Mock _translate_with_llm which is called by the internal fallback
    async def _fake_translate_llm(text: str, source_lang: str, target_lang: str, model: str) -> str:
        return f"fallback:{text}"

    monkeypatch.setattr(translator, "_translate_with_llm", _fake_translate_llm)

    results = await translator._translate_batch_llm(["uno", "dos"], "es", "en", model="gpt-4o-mini")

    assert results == ["fallback:uno", "fallback:dos"]


@pytest.mark.asyncio
async def test_translate_batch_preserves_order_and_skips_same_language(monkeypatch) -> None:
    translator = LLMTranslator()
    lang_map = {"hola": "es", "bonjour": "fr", "hello": "en", "ciao": "it"}

    async def _fake_detect_language(text: str) -> str:
        return lang_map[text]

    async def _fake_batch(texts: list[str], source_lang: str, target_lang: str, model: str) -> list[str]:
        return [f"{source_lang}->{target_lang}:{text}" for text in texts]

    monkeypatch.setattr(translator, "detect_language", _fake_detect_language)
    monkeypatch.setattr(translator, "_translate_batch_llm", _fake_batch)

    results = await translator.translate_batch(
        ["hola", "bonjour", "hello", "ciao"],
        target_lang="en",
    )

    assert results == [
        ("es->en:hola", "es", "normal"),
        ("fr->en:bonjour", "fr", "normal"),
        ("hello", "en", "skip"),
        ("it->en:ciao", "it", "normal"),
    ]
