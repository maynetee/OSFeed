from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
from openai import AsyncOpenAI
from app.config import get_settings
from app.services.usage import record_api_usage
from app.services.cache import get_redis_client
from typing import Optional
import asyncio
import hashlib

settings = get_settings()


class LLMTranslator:
    def __init__(self):
        self.target_language = settings.preferred_language
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.cache = {}
        self._client = None
        self._redis = get_redis_client()

    @property
    def client(self) -> Optional[AsyncOpenAI]:
        if not self.api_key:
            return None
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key, timeout=30.0)
        return self._client

    def detect_language(self, text: str) -> str:
        """Detect the language of given text."""
        try:
            if not text or len(text.strip()) < 10:
                return "unknown"
            return detect(text)
        except LangDetectException:
            return "unknown"

    def _cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{source_lang}:{target_lang}:{text_hash}"

    def _chunk_text(self, text: str, chunk_size: int = 3500) -> list[str]:
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    async def _translate_with_google(self, text: str, source_lang: str, target_lang: str) -> str:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        return await asyncio.to_thread(translator.translate, text)

    async def _translate_with_llm(self, text: str, source_lang: str, target_lang: str) -> str:
        client = self.client
        if client is None:
            raise RuntimeError("OpenAI API key is not configured")

        chunks = self._chunk_text(text)
        translated_chunks = []

        for chunk in chunks:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional OSINT translator. "
                            "Preserve names, dates, numbers, URLs, and tone. "
                            "Return only the translated text with no extra commentary."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Source language: {source_lang}\n"
                            f"Target language: {target_lang}\n\n"
                            f"Text:\n{chunk}"
                        ),
                    },
                ],
                temperature=0.2,
            )
            translated_chunks.append(response.choices[0].message.content.strip())
            if response.usage:
                await record_api_usage(
                    provider="openai",
                    model=self.model,
                    purpose="translation",
                    prompt_tokens=response.usage.prompt_tokens or 0,
                    completion_tokens=response.usage.completion_tokens or 0,
                    metadata={"chunk_length": len(chunk)},
                )

        return "".join(translated_chunks)

    async def translate(
        self,
        text: str,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Translate text to target language (async).
        Returns (translated_text, source_language).
        """
        if not text or len(text.strip()) == 0:
            return text, "unknown"

        if not target_lang:
            target_lang = self.target_language

        if not source_lang or source_lang == "unknown":
            source_lang = self.detect_language(text)

        if source_lang == target_lang or source_lang == "unknown":
            return text, source_lang

        cache_key = self._cache_key(text, source_lang, target_lang)
        if self._redis is not None:
            try:
                cached = await self._redis.get(cache_key)
                if cached:
                    return cached, source_lang
            except Exception:
                pass
        if cache_key in self.cache:
            return self.cache[cache_key], source_lang

        try:
            translated_text = await self._translate_with_llm(text, source_lang, target_lang)
        except Exception as e:
            print(f"LLM translation failed: {e}")
            try:
                translated_text = await self._translate_with_google(text, source_lang, target_lang)
            except Exception as fallback_error:
                print(f"Fallback translation failed: {fallback_error}")
                return text, source_lang

        if self._redis is not None:
            try:
                await self._redis.set(
                    cache_key,
                    translated_text,
                    ex=settings.redis_cache_ttl_seconds,
                )
            except Exception:
                self.cache[cache_key] = translated_text
        else:
            self.cache[cache_key] = translated_text
        return translated_text, source_lang


# Singleton instance
translator = LLMTranslator()
