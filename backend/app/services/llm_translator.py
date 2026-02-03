import asyncio
import hashlib
import logging
import re
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import httpx
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import MessageTranslation

from app.config import get_settings
from app.services.cache import get_redis_client, increment_translation_cache_hit, increment_translation_cache_miss
from app.services.usage import record_api_usage

logger = logging.getLogger(__name__)

# Batch translation constants
BATCH_SEPARATOR = "\n\n<<<MSG_SEP>>>\n\n"
MAX_BATCH_SIZE = 100  # Messages per batch
MAX_BATCH_CHARS = 10000  # Max characters per batch to stay within token limits

settings = get_settings()

SKIP_REGEXES = [
    re.compile(r"^https?://\S+$", re.IGNORECASE),
    re.compile(r"^[@#]\w+$"),
    re.compile(r"^\d+$"),
    re.compile(r"^[^\w\s]{1,10}$"),
]


class LLMTranslator:
    def __init__(self):
        self.target_language = settings.preferred_language
        self.api_key = settings.openai_api_key
        self.openai_model = settings.openai_model
        self.gemini_api_key = settings.gemini_api_key
        self.gemini_model = settings.gemini_model
        self.cache: OrderedDict[str, tuple[str, int]] = OrderedDict()
        self._client = None
        self._redis = get_redis_client()

    @property
    def client(self) -> Optional[AsyncOpenAI]:
        if not self.api_key:
            return None
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key, timeout=30.0)
        return self._client

    async def detect_language(self, text: str) -> str:
        """Detect the language of given text (async)."""
        try:
            if not text or len(text.strip()) < 10:
                return "unknown"
            return await asyncio.to_thread(detect, text)
        except LangDetectException:
            return "unknown"

    def _is_trivial_text(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped:
            return True
        if settings.translation_skip_trivial:
            for pattern in SKIP_REGEXES:
                if pattern.match(stripped):
                    return True
            short_words = {w.lower() for w in settings.translation_skip_short_words}
            if stripped.lower() in short_words:
                return True
            if (
                settings.translation_skip_short_max_chars > 0
                and len(stripped) <= settings.translation_skip_short_max_chars
                and stripped.isalpha()
            ):
                return True
        return False

    def _priority_by_age(self, published_at: Optional[datetime]) -> str:
        if not published_at:
            return "normal"
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age = now - published_at
        if age <= timedelta(hours=settings.translation_high_priority_hours):
            return "high"
        if age <= timedelta(days=settings.translation_normal_priority_days):
            return "normal"
        return "low"

    def get_translation_priority(
        self,
        text: str,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
        published_at: Optional[datetime] = None,
    ) -> str:
        if not text or not text.strip():
            return "skip"
        if self._is_trivial_text(text):
            return "skip"
        if not target_lang:
            target_lang = self.target_language
        if settings.translation_skip_same_language and source_lang == target_lang:
            return "skip"
        return self._priority_by_age(published_at)

    def _cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        # Use SHA256 for better performance/collision resistance than MD5
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"{source_lang}:{target_lang}:{text_hash}"

    def _cache_hit_key(self, cache_key: str) -> str:
        return f"{cache_key}:hits"

    def _adaptive_ttl(self, hit_count: int) -> int:
        base_ttl = settings.translation_cache_base_ttl
        max_ttl = settings.translation_cache_max_ttl
        multiplier = settings.translation_cache_hit_multiplier
        ttl = int(base_ttl * (1 + (hit_count * multiplier)))
        return min(max(ttl, base_ttl), max_ttl)

    def _chunk_text(self, text: str, chunk_size: int = 3500) -> list[str]:
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    async def _translate_with_google(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using Google Translate (via deep-translator library).

        This is a free translation method with no API key required.
        Uses asyncio.to_thread to run the synchronous GoogleTranslator in a thread pool.

        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en', 'es', 'fr')
            target_lang: Target language code (e.g., 'en', 'es', 'fr')

        Returns:
            Translated text string

        Raises:
            Exception: If translation fails (propagated from GoogleTranslator)
        """
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        return await asyncio.to_thread(translator.translate, text)

    async def _translate_with_llm(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        model: str,
    ) -> str:
        """Translate text using OpenAI LLM (GPT models).

        Automatically chunks large texts (>3500 chars) to stay within token limits.
        Uses a specialized OSINT translation prompt that preserves names, dates, URLs, and numbers.
        Records API usage metrics for cost tracking.

        Args:
            text: Text to translate (will be chunked if > 3500 chars)
            source_lang: Source language code (e.g., 'en', 'es', 'fr')
            target_lang: Target language code (e.g., 'en', 'es', 'fr')
            model: OpenAI model to use (e.g., 'gpt-4', 'gpt-3.5-turbo')

        Returns:
            Translated text string (chunks rejoined if text was chunked)

        Raises:
            RuntimeError: If OpenAI API key is not configured
            Exception: If API call fails (propagated from OpenAI client)
        """
        client = self.client
        if client is None:
            raise RuntimeError("OpenAI API key is not configured")

        chunks = self._chunk_text(text)
        translated_chunks = []

        for chunk in chunks:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "OSINT translator. Keep names, dates, URLs, numbers. "
                            "Return only the translation."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Translate from {source_lang} to {target_lang}:\n{chunk}"
                        ),
                    },
                ],
                temperature=0.2,
            )
            translated_chunks.append(response.choices[0].message.content.strip())
            if response.usage:
                await record_api_usage(
                    provider="openai",
                    model=model,
                    purpose="translation",
                    prompt_tokens=response.usage.prompt_tokens or 0,
                    completion_tokens=response.usage.completion_tokens or 0,
                    metadata={"chunk_length": len(chunk)},
                )

        return "".join(translated_chunks)

    async def _translate_with_gemini(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        model: str,
    ) -> str:
        """Translate text using Google Gemini LLM API.

        Uses httpx to make direct API calls to Gemini's REST endpoint.
        Uses the same specialized OSINT translation prompt as OpenAI method
        to preserve names, dates, URLs, and numbers.

        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en', 'es', 'fr')
            target_lang: Target language code (e.g., 'en', 'es', 'fr')
            model: Gemini model to use (e.g., 'gemini-pro', from settings.gemini_model)

        Returns:
            Translated text string

        Raises:
            RuntimeError: If Gemini API key is not configured, or if API returns no candidates/text
            httpx.HTTPStatusError: If API request fails (from response.raise_for_status())
        """
        if not self.gemini_api_key:
            raise RuntimeError("Gemini API key is not configured")
        prompt = (
            "OSINT translator. Keep names, dates, URLs, numbers. "
            f"Translate from {source_lang} to {target_lang}. "
            "Return only the translation.\n\n"
            f"{text}"
        )
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        )
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": prompt}]},
            ],
            "generationConfig": {"temperature": 0.2},
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params={"key": self.gemini_api_key}, json=payload)
            response.raise_for_status()
            data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini translation returned no candidates")
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts or "text" not in parts[0]:
            raise RuntimeError("Gemini translation returned no text")
        return parts[0]["text"].strip()

    def _select_model(self, source_lang: str, priority: str) -> str:
        if priority == "high":
            return settings.translation_high_priority_model
        if source_lang in settings.translation_high_quality_languages and priority != "low":
            return settings.translation_high_priority_model
        return settings.translation_default_model

    def _resolve_model(self, model_name: str) -> tuple[str, str]:
        normalized = model_name.lower()
        if normalized in {"google", "google-translate"}:
            return "google", "google"
        if normalized.startswith("gemini"):
            if self.gemini_api_key:
                return "gemini", self.gemini_model
            if self.api_key:
                return "openai", self.openai_model
            return "google", "google"
        if self.api_key:
            return "openai", model_name
        if self.gemini_api_key:
            return "gemini", self.gemini_model
        return "google", "google"

    async def _get_from_cache(self, cache_key: str) -> Optional[str]:
        if self._redis is not None:
            try:
                cached = await self._redis.get(cache_key)
                if cached:
                    hit_key = self._cache_hit_key(cache_key)
                    hits = int(await self._redis.get(hit_key) or 0) + 1
                    ttl = self._adaptive_ttl(hits)
                    await self._redis.set(hit_key, hits, ex=ttl)
                    await self._redis.expire(cache_key, ttl)
                    await increment_translation_cache_hit()
                    return cached
            except Exception:
                pass
        if cache_key in self.cache:
            cached, hits = self.cache[cache_key]
            self.cache[cache_key] = (cached, hits + 1)
            self.cache.move_to_end(cache_key)
            return cached
        return None

    async def translate(
        self,
        text: str,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
        published_at: Optional[datetime] = None,
        db: Optional[Session] = None,
        message_id: Optional[UUID] = None,
    ) -> tuple[str, str, str]:
        """
        Translate text to target language (async).
        Returns (translated_text, source_language, priority).
        """
        if not text or len(text.strip()) == 0:
            return text, "unknown", "skip"
        if self._is_trivial_text(text):
            return text, "unknown", "skip"

        if not target_lang:
            target_lang = self.target_language

        if not source_lang or source_lang == "unknown":
            source_lang = await self.detect_language(text)

        priority = self.get_translation_priority(
            text,
            source_lang=source_lang,
            target_lang=target_lang,
            published_at=published_at,
        )
        if priority == "skip":
            return text, source_lang, "skip"

        cache_key = self._cache_key(text, source_lang, target_lang)

        # Three-tier cache lookup strategy: DB -> Redis -> Memory
        # This layered approach provides different trade-offs:
        # - DB: Persistent, shared across instances, but slower
        # - Redis: Fast, shared across instances, but volatile
        # - Memory: Fastest, but instance-local and limited by RAM

        # Tier 1: Database cache lookup
        # Check if this specific message has already been translated and persisted.
        # This is the most reliable cache but slowest to access.
        if db and message_id:
            stmt = select(MessageTranslation.translated_text).where(
                MessageTranslation.message_id == message_id,
                MessageTranslation.target_lang == target_lang,
            )
            try:
                db_translation = db.execute(stmt).scalar_one_or_none()
                if db_translation:
                    # Cache hit in DB - return immediately without checking other tiers
                    return db_translation, source_lang, priority
            except Exception as e:
                # DB lookup failures are non-fatal - fall through to next cache tier
                logger.warning(f"DB translation lookup failed: {e}")

        # Tier 2 & 3: Redis and in-memory cache lookup
        # _get_from_cache checks Redis first (if available), then falls back to memory cache.
        # Redis provides cross-instance caching with adaptive TTL based on hit count.
        # Memory cache provides ultra-fast access for frequently used translations.
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached, source_lang, priority

        # Cache miss across all tiers - need to perform actual translation
        await increment_translation_cache_miss()
        # Select appropriate model based on language and priority
        model_name = self._select_model(source_lang, priority)
        provider, resolved_model = self._resolve_model(model_name)

        # Translation fallback chain: Primary provider -> Google Translate -> Original text
        # This ensures maximum availability while preferring higher quality LLM translations
        try:
            # Try primary translation provider (OpenAI, Gemini, or Google)
            if provider == "openai":
                translated_text = await self._translate_with_llm(
                    text, source_lang, target_lang, resolved_model
                )
            elif provider == "gemini":
                translated_text = await self._translate_with_gemini(
                    text, source_lang, target_lang, resolved_model
                )
            else:
                # Already using Google as primary - no fallback needed
                translated_text = await self._translate_with_google(text, source_lang, target_lang)
        except Exception as e:
            # Primary provider failed - fall back to free Google Translate
            logger.error(f"LLM translation failed: {e}")
            try:
                translated_text = await self._translate_with_google(text, source_lang, target_lang)
            except Exception as fallback_error:
                # All translation methods failed - return original text unchanged
                # This ensures the application continues functioning even when translation fails
                logger.error(f"Fallback translation failed (All methods): {fallback_error}")
                return text, source_lang, priority

        await self._cache_translation(text, translated_text, source_lang, target_lang)
        return translated_text, source_lang, priority

    async def translate_batch(
        self,
        texts: list[str],
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
        published_at_list: Optional[list[datetime]] = None,
        db: Optional[Session] = None,
        message_ids: Optional[list[UUID]] = None,
    ) -> list[tuple[str, str, str]]:
        """
        Translate multiple texts in a single API call for efficiency.
        Returns list of (translated_text, source_language, priority) tuples preserving input order.
        """
        if not texts:
            return []

        target_lang = target_lang or self.target_language
        # Pre-allocate results array to preserve input order
        results: list[tuple[str, str, str]] = [("", "unknown", "skip")] * len(texts)
        published_at_list = published_at_list or []

        # Ensure message_ids length matches if provided
        if message_ids and len(message_ids) != len(texts):
            logger.warning("message_ids length mismatch with texts, ignoring message_ids")
            message_ids = None

        # Step 1: Categorize texts - filter out skippable content and prepare for translation
        # This step reduces unnecessary API calls by:
        # - Detecting language for each text (unless already known)
        # - Calculating priority based on content age
        # - Filtering out trivial content (URLs, short words, etc.)
        # - Filtering out same-language content (if configured)
        # Store tuple: (index, text, detected_lang, priority, message_id)
        to_translate_info: list[tuple[int, str, str, str, Optional[UUID]]] = []

        for i, text in enumerate(texts):
            msg_id = message_ids[i] if message_ids else None

            # Skip empty or whitespace-only texts
            if not text or not text.strip():
                results[i] = (text or "", "unknown", "skip")
                continue

            # Skip trivial content (URLs, hashtags, numbers, short words)
            if self._is_trivial_text(text):
                results[i] = (text, "unknown", "skip")
                continue

            # Detect language if not explicitly provided
            # Reuse source_lang across batch if provided to avoid redundant detection
            if source_lang:
                detected = source_lang
            else:
                detected = await self.detect_language(text)

            # Calculate translation priority based on content age
            published_at = published_at_list[i] if i < len(published_at_list) else None
            priority = self.get_translation_priority(
                text,
                source_lang=detected,
                target_lang=target_lang,
                published_at=published_at,
            )

            # Skip same-language content (if configured)
            if priority == "skip":
                results[i] = (text, detected, priority)
                continue

            # Add to translation queue with metadata for cache lookups
            to_translate_info.append((i, text, detected, priority, msg_id))

        logger.info(f"DEBUG: translate_batch: {len(to_translate_info)} items to translate after filtering")

        # Early return if all texts were filtered out
        if not to_translate_info:
            return results

        # Step 2: Tier 1 Cache - Bulk DB cache lookup
        # For batch operations, we can efficiently query multiple translations in one DB call
        # This is faster than N individual queries and provides persistent cross-instance caching
        uncached_after_db: list[tuple[int, str, str, str, Optional[UUID]]] = []

        if db:
            # Gather message IDs for bulk database query
            # Only check items that have associated message_ids
            ids_to_check = [item[4] for item in to_translate_info if item[4] is not None]
            db_map = {}

            if ids_to_check:
                try:
                    # Single bulk query for all message translations
                    stmt = select(MessageTranslation.message_id, MessageTranslation.translated_text).where(
                        MessageTranslation.message_id.in_(ids_to_check),
                        MessageTranslation.target_lang == target_lang
                    )
                    rows = db.execute(stmt).all()
                    # Build lookup map for O(1) access
                    db_map = {row.message_id: row.translated_text for row in rows}
                except Exception as e:
                    # DB failures are non-fatal - continue to next cache tier
                    logger.warning(f"Batch DB lookup failed: {e}")

            # Separate cached vs uncached items
            for item in to_translate_info:
                idx, text, lang, prio, mid = item
                if mid and mid in db_map:
                    # DB cache hit - store result and skip further processing
                    results[idx] = (db_map[mid], lang, prio)
                else:
                    # DB cache miss - proceed to next cache tier
                    uncached_after_db.append(item)
        else:
            # No DB session - skip DB cache tier entirely
            uncached_after_db = to_translate_info

        # Early return if all translations found in DB cache
        if not uncached_after_db:
            return results

        # Step 3: Tier 2 & 3 Cache - Redis and in-memory cache lookup
        # Check each uncached text against Redis (shared, fast) and memory (local, fastest)
        # These caches use content-based keys (hash of text + languages) rather than message IDs,
        # so they can cache translations even for texts without persistent message records
        uncached_final: list[tuple[int, str, str, str]] = []

        for item in uncached_after_db:
            idx, text, lang, prio, mid = item
            # Generate content-based cache key from text hash and language pair
            cache_key = self._cache_key(text, lang, target_lang)
            # _get_from_cache checks Redis first, then falls back to memory cache
            cached_text = await self._get_from_cache(cache_key)

            if cached_text:
                # Cache hit in Redis or memory - store result
                results[idx] = (cached_text, lang, prio)
            else:
                # Complete cache miss across all tiers - needs actual translation
                # Drop message_id since it's not needed for translation
                uncached_final.append((idx, text, lang, prio))

        # Early return if all translations found in Redis/memory cache
        if not uncached_final:
            return results

        # Step 4: Group by translation route (source language + model)
        # Texts with the same source language and model can be batched together in a single API call
        # This significantly reduces API costs and latency compared to individual translations
        by_route: dict[tuple[str, str], list[tuple[int, str, str]]] = {}
        for i, text, lang, priority in uncached_final:
            # Select appropriate model based on language and priority
            model_name = self._select_model(lang, priority)
            # Group by (source_lang, model) tuple to enable efficient batching
            by_route.setdefault((lang, model_name), []).append((i, text, priority))

        # Step 5: Execute batch translations with fallback handling
        # Process each route group independently, respecting batch size and character limits
        for (src_lang, model_name), items in by_route.items():
            # Split items into batches respecting MAX_BATCH_SIZE and MAX_BATCH_CHARS
            batches = self._create_batches([(idx, text) for idx, text, _ in items])

            for batch in batches:
                indices = [idx for idx, _ in batch]
                batch_texts = [txt for _, txt in batch]

                # Build priority lookup for storing results
                priorities_by_index = {
                    idx: priority for idx, _, priority in items if idx in indices
                }

                # Resolve model name to actual provider and model
                provider, resolved_model = self._resolve_model(model_name)

                translated_batch: list[str] = []
                success = False

                # Translation fallback chain for batches: Batch API -> Individual parallel -> Original text
                # First, try the batch translation API for the selected provider
                try:
                    if provider == "openai":
                        # Single API call for entire batch using separator-based approach
                        translated_batch = await self._translate_batch_llm(
                            batch_texts, src_lang, target_lang, resolved_model
                        )
                    elif provider == "gemini":
                        # Single API call for entire batch using separator-based approach
                        translated_batch = await self._translate_batch_gemini(
                            batch_texts, src_lang, target_lang, resolved_model
                        )
                    else:
                        # Google Translate doesn't have true batch API - translate sequentially
                        translated_batch = []
                        for txt in batch_texts:
                            translated_batch.append(
                                await self._translate_with_google(txt, src_lang, target_lang)
                            )

                    # Validate response contains expected number of translations
                    if len(translated_batch) != len(batch_texts):
                        raise ValueError(f"Translation length mismatch: {len(translated_batch)} vs {len(batch_texts)}")

                    success = True

                except Exception as e:
                    # Batch translation failed - will fall back to individual translations
                    logger.warning(f"Batch translation failed ({provider}), falling back to parallel individual: {e}")

                if success:
                    # Batch translation succeeded - store results and update caches
                    for idx, orig_text, trans_text in zip(indices, batch_texts, translated_batch):
                        priority = priorities_by_index.get(idx, "normal")
                        results[idx] = (trans_text, src_lang, priority)
                        # Fire-and-forget cache update (non-blocking)
                        asyncio.create_task(self._cache_translation(orig_text, trans_text, src_lang, target_lang))
                else:
                    # Fallback: Translate each text individually in parallel
                    # Use translate() method which has its own fallback chain (LLM -> Google -> Original)
                    fallback_tasks = []
                    for txt in batch_texts:
                        fallback_tasks.append(self.translate(txt, src_lang, target_lang))

                    # Execute all individual translations concurrently
                    fallback_results = await asyncio.gather(*fallback_tasks, return_exceptions=True)

                    # Process fallback results
                    for idx, res in zip(indices, fallback_results):
                        if isinstance(res, Exception):
                            # Individual translation also failed - return original text
                            logger.error(f"Individual fallback failed for item {idx}: {res}")
                            results[idx] = (batch_texts[indices.index(idx)], src_lang, "normal")
                        else:
                            # Individual translation succeeded - res is (text, lang, priority)
                            results[idx] = res

        return results

    def _create_batches(
        self, items: list[tuple[int, str]]
    ) -> list[list[tuple[int, str]]]:
        """Split items into batches respecting size and character limits.

        Creates batches of text items for efficient batch translation while
        staying within API limits. Each batch respects both:
        - MAX_BATCH_SIZE (100 messages per batch)
        - MAX_BATCH_CHARS (10000 characters per batch)

        The batches preserve the original index mapping to allow results
        to be correctly assigned back to the original input order.

        Args:
            items: List of (index, text) tuples to batch, where index
                   is the original position in the input list

        Returns:
            List of batches, where each batch is a list of (index, text) tuples
        """
        batches = []
        current_batch = []
        current_chars = 0

        for item in items:
            idx, text = item
            text_len = len(text)

            # Check if adding this text exceeds limits
            if current_batch and (
                len(current_batch) >= MAX_BATCH_SIZE
                or current_chars + text_len > MAX_BATCH_CHARS
            ):
                batches.append(current_batch)
                current_batch = []
                current_chars = 0

            current_batch.append(item)
            current_chars += text_len + len(BATCH_SEPARATOR)

        if current_batch:
            batches.append(current_batch)

        return batches

    async def _translate_batch_llm(
        self,
        texts: list[str],
        source_lang: str,
        target_lang: str,
        model: str,
    ) -> list[str]:
        """Translate multiple texts in a single OpenAI LLM API call.

        Uses a batch translation strategy to reduce API costs and latency:
        1. Combines all texts with BATCH_SEPARATOR delimiter
        2. Sends combined text in single API call
        3. Splits response on separator to extract individual translations
        4. Records API usage metrics for the entire batch

        If the response doesn't contain the expected number of translations,
        automatically falls back to individual translation for each text.

        Uses the same OSINT translation prompt as _translate_with_llm to
        preserve names, dates, URLs, and numbers.

        Args:
            texts: List of texts to translate
            source_lang: Source language code (e.g., 'en', 'es', 'fr')
            target_lang: Target language code (e.g., 'en', 'es', 'fr')
            model: OpenAI model to use (e.g., 'gpt-4', 'gpt-3.5-turbo')

        Returns:
            List of translated texts in same order as input

        Raises:
            RuntimeError: If OpenAI API key is not configured
            Exception: If API call fails (propagated from OpenAI client)
        """
        if not texts:
            return []

        client = self.client
        if client is None:
            raise RuntimeError("OpenAI API key is not configured")

        # Combine texts with unique separator
        combined = BATCH_SEPARATOR.join(texts)

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "OSINT translator. Translate each segment. "
                        "Keep separator <<<MSG_SEP>>>. "
                        "Preserve names, dates, URLs, numbers. Return only translations."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Translate from {source_lang} to {target_lang}:\n\n{combined}"
                    ),
                },
            ],
            temperature=0.2,
        )

        result = response.choices[0].message.content.strip()

        # Record API usage for the batch
        if response.usage:
            await record_api_usage(
                provider="openai",
                model=model,
                purpose="translation_batch",
                prompt_tokens=response.usage.prompt_tokens or 0,
                completion_tokens=response.usage.completion_tokens or 0,
                metadata={
                    "batch_size": len(texts),
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "total_chars": len(combined),
                },
            )

        # Parse the results by splitting on separator
        translated = result.split(BATCH_SEPARATOR)

        # Verify count matches
        if len(translated) != len(texts):
            logger.warning(
                f"Batch translation mismatch: expected {len(texts)}, got {len(translated)}. "
                "Falling back to individual translation."
            )
            # Fallback: translate each text individually
            fallback_results = []
            for text in texts:
                trans_text = await self._translate_with_llm(text, source_lang, target_lang, model)
                fallback_results.append(trans_text)
            return fallback_results

        return [t.strip() for t in translated]

    async def _translate_batch_gemini(
        self,
        texts: list[str],
        source_lang: str,
        target_lang: str,
        model: str,
    ) -> list[str]:
        """Translate multiple texts in a single Google Gemini API call.

        Uses a batch translation strategy similar to _translate_batch_llm:
        1. Combines all texts with BATCH_SEPARATOR delimiter
        2. Sends combined text to Gemini's REST endpoint
        3. Splits response on separator to extract individual translations

        Unlike the OpenAI method, this raises an error instead of falling back
        if the response doesn't contain the expected number of translations.
        The caller should handle this by using individual translation fallback.

        Uses the same OSINT translation prompt to preserve names, dates,
        URLs, and numbers.

        Args:
            texts: List of texts to translate
            source_lang: Source language code (e.g., 'en', 'es', 'fr')
            target_lang: Target language code (e.g., 'en', 'es', 'fr')
            model: Gemini model to use (e.g., 'gemini-pro', from settings.gemini_model)

        Returns:
            List of translated texts in same order as input

        Raises:
            RuntimeError: If Gemini API key is not configured, if API returns
                         no candidates/text, or if translation count mismatch
            httpx.HTTPStatusError: If API request fails (from response.raise_for_status())
        """
        if not texts:
            return []
        if not self.gemini_api_key:
            raise RuntimeError("Gemini API key is not configured")

        combined = BATCH_SEPARATOR.join(texts)
        prompt = (
            "OSINT translator. Translate each segment. Keep separator <<<MSG_SEP>>>. "
            f"Translate from {source_lang} to {target_lang}. "
            "Preserve names, dates, URLs, numbers. Return only translations.\n\n"
            f"{combined}"
        )
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        )
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2},
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params={"key": self.gemini_api_key}, json=payload)
            response.raise_for_status()
            data = response.json()

        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini batch translation returned no candidates")
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts or "text" not in parts[0]:
            raise RuntimeError("Gemini batch translation returned no text")
        result = parts[0]["text"].strip()
        translated = result.split(BATCH_SEPARATOR)

        if len(translated) != len(texts):
            raise RuntimeError(
                f"Gemini batch translation mismatch: {len(translated)} vs {len(texts)}"
            )

        return [t.strip() for t in translated]

    async def _cache_translation(
        self, original: str, translated: str, source_lang: str, target_lang: str
    ) -> None:
        """Cache a translation result."""
        # Use simple hex SHA256
        cache_key = self._cache_key(original, source_lang, target_lang)
        if self._redis is not None:
            try:
                ttl = self._adaptive_ttl(1)
                await self._redis.set(cache_key, translated, ex=ttl)
                await self._redis.set(self._cache_hit_key(cache_key), 1, ex=ttl)
            except Exception:
                # LRU eviction: remove oldest entry if cache is full
                if len(self.cache) >= settings.translation_memory_cache_max_size:
                    self.cache.popitem(last=False)
                self.cache[cache_key] = (translated, 1)
        else:
            # LRU eviction: remove oldest entry if cache is full
            if len(self.cache) >= settings.translation_memory_cache_max_size:
                self.cache.popitem(last=False)
            self.cache[cache_key] = (translated, 1)


# Singleton instance
translator = LLMTranslator()
