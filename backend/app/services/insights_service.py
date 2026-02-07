"""Intelligence Insights Service - AI-powered dashboard insights from OSINT messages.

Provides real-time signal counting, AI-generated intelligence tips,
trending topic extraction, and activity spike detection.
"""

import logging
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from redis.exceptions import RedisError
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.channel import Channel, user_channels
from app.models.message import Message
from app.services.cache import get_redis_client

logger = logging.getLogger(__name__)
settings = get_settings()

# Stop words for trending topic extraction
STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "because", "but", "and", "or", "if", "while", "about", "up", "its",
    "it", "this", "that", "these", "those", "i", "me", "my", "we", "our",
    "you", "your", "he", "him", "his", "she", "her", "they", "them", "their",
    "what", "which", "who", "whom", "whose", "le", "la", "les", "de", "du",
    "des", "un", "une", "et", "en", "est", "que", "qui", "dans", "pour",
    "sur", "par", "avec", "plus", "pas", "ce", "se", "au", "aux", "son",
    "sa", "ses", "nous", "vous", "ils", "elle", "elles", "ont", "sont",
})

# Regex for extracting words
WORD_RE = re.compile(r"[a-zA-Z\u00C0-\u024F]{3,}")

INSIGHTS_TIPS_CACHE_KEY = "insights:tips:{user_id}"
INSIGHTS_TIPS_TTL = 1800  # 30 minutes


class InsightsService:
    """Service for generating AI intelligence insights from user's OSINT data."""

    async def get_signals_processed(self, user_id: UUID, db: AsyncSession) -> dict:
        """Get real message counts: today, this_week, all_time."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        # Use conditional aggregation for all three counts in one query
        result = await db.execute(
            select(
                func.count().label("all_time"),
                func.coalesce(
                    func.sum(case((Message.published_at >= today_start, 1), else_=0)),
                    0,
                ).label("today"),
                func.coalesce(
                    func.sum(case((Message.published_at >= week_start, 1), else_=0)),
                    0,
                ).label("this_week"),
            )
            .select_from(Message)
            .join(Channel, Message.channel_id == Channel.id)
            .join(user_channels, and_(
                user_channels.c.channel_id == Channel.id,
                user_channels.c.user_id == user_id,
            ))
        )
        row = result.first()
        return {
            "today": row.today if row else 0,
            "this_week": row.this_week if row else 0,
            "all_time": row.all_time if row else 0,
        }

    async def generate_intelligence_tips(self, user_id: UUID, db: AsyncSession) -> list[dict]:
        """Generate 3-5 AI intelligence tips from recent messages using Gemini Flash."""
        # Check Redis cache first
        redis = get_redis_client()
        cache_key = INSIGHTS_TIPS_CACHE_KEY.format(user_id=user_id)

        if redis is not None:
            try:
                cached = await redis.get(cache_key)
                if cached:
                    import json
                    return json.loads(cached)
            except (RedisError, Exception):
                pass

        # Query last 100 translated messages from user's channels
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        result = await db.execute(
            select(Message.translated_text, Message.original_text, Channel.title)
            .join(Channel, Message.channel_id == Channel.id)
            .join(user_channels, and_(
                user_channels.c.channel_id == Channel.id,
                user_channels.c.user_id == user_id,
            ))
            .where(Message.published_at >= week_ago)
            .where(Message.is_duplicate == False)  # noqa: E712
            .order_by(Message.published_at.desc())
            .limit(100)
        )
        rows = result.all()

        if not rows:
            return []

        # Build context from messages
        message_texts = []
        for row in rows[:50]:  # Use top 50 for the prompt
            text = row.translated_text or row.original_text or ""
            if text.strip():
                message_texts.append(f"[{row.title}]: {text[:200]}")

        if not message_texts:
            return []

        context = "\n".join(message_texts)

        # Call Gemini Flash for intelligence tips
        tips = await self._call_gemini_for_tips(context)

        # Cache in Redis for 30 min
        if redis is not None and tips:
            try:
                import json
                await redis.set(cache_key, json.dumps(tips), ex=INSIGHTS_TIPS_TTL)
            except (RedisError, Exception):
                pass

        return tips

    async def _call_gemini_for_tips(self, context: str) -> list[dict]:
        """Call Gemini Flash API to generate intelligence tips."""
        if not settings.gemini_api_key:
            return self._fallback_tips()

        prompt = (
            "You are an OSINT intelligence analyst. Based on these recent messages from "
            "monitored Telegram channels, generate exactly 3-5 brief intelligence tips. "
            "Each tip should highlight a notable pattern, emerging trend, or actionable insight.\n\n"
            "Return ONLY a JSON array with objects having these fields:\n"
            '- "title": short title (max 10 words)\n'
            '- "description": brief explanation (max 30 words)\n'
            '- "severity": one of "info", "warning", "critical"\n\n'
            "Messages:\n"
            f"{context[:4000]}\n\n"
            "Return ONLY the JSON array, no markdown formatting or code blocks."
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4},
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, params={"key": settings.gemini_api_key}, json=payload)
                response.raise_for_status()
                data = response.json()

            candidates = data.get("candidates") or []
            if not candidates:
                return self._fallback_tips()

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts or "text" not in parts[0]:
                return self._fallback_tips()

            raw_text = parts[0]["text"].strip()
            # Strip markdown code blocks if present
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)

            import json
            tips = json.loads(raw_text)

            # Validate structure
            valid_tips = []
            for tip in tips[:5]:
                if isinstance(tip, dict) and "title" in tip and "description" in tip:
                    valid_tips.append({
                        "title": str(tip["title"])[:100],
                        "description": str(tip["description"])[:200],
                        "severity": tip.get("severity", "info")
                        if tip.get("severity") in ("info", "warning", "critical") else "info",
                    })

            return valid_tips if valid_tips else self._fallback_tips()

        except Exception as e:
            logger.warning(f"Gemini intelligence tips generation failed: {e}")
            return self._fallback_tips()

    def _fallback_tips(self) -> list[dict]:
        """Return fallback tips when AI generation is unavailable."""
        return [
            {
                "title": "Monitor active channels",
                "description": "Review your most active channels for emerging patterns.",
                "severity": "info",
            },
            {
                "title": "Check translation queue",
                "description": "Ensure pending translations are processing to avoid intelligence gaps.",
                "severity": "info",
            },
        ]

    async def get_trending_topics(self, user_id: UUID, db: AsyncSession) -> list[dict]:
        """Extract top 5 trending topics from recent translated messages."""
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(days=1)

        result = await db.execute(
            select(Message.translated_text)
            .join(Channel, Message.channel_id == Channel.id)
            .join(user_channels, and_(
                user_channels.c.channel_id == Channel.id,
                user_channels.c.user_id == user_id,
            ))
            .where(Message.published_at >= day_ago)
            .where(Message.translated_text.isnot(None))
            .where(Message.is_duplicate == False)  # noqa: E712
            .limit(500)
        )
        rows = result.scalars().all()

        # Word frequency analysis
        word_counts: Counter = Counter()
        for text in rows:
            if not text:
                continue
            words = WORD_RE.findall(text.lower())
            for word in words:
                if word not in STOP_WORDS and len(word) >= 4:
                    word_counts[word] += 1

        # Return top 5
        return [
            {"topic": word, "count": count}
            for word, count in word_counts.most_common(5)
        ]

    async def detect_activity_spikes(self, user_id: UUID, db: AsyncSession) -> list[dict]:
        """Detect channels with >2x average message volume."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today_start - timedelta(days=7)

        # Get today's count and 7-day average per channel
        result = await db.execute(
            select(
                Channel.id,
                Channel.title,
                func.coalesce(
                    func.sum(case((Message.published_at >= today_start, 1), else_=0)),
                    0,
                ).label("today_count"),
                func.coalesce(
                    func.sum(case((Message.published_at >= week_ago, 1), else_=0)),
                    0,
                ).label("week_count"),
            )
            .select_from(Message)
            .join(Channel, Message.channel_id == Channel.id)
            .join(user_channels, and_(
                user_channels.c.channel_id == Channel.id,
                user_channels.c.user_id == user_id,
            ))
            .where(Message.published_at >= week_ago)
            .group_by(Channel.id, Channel.title)
        )
        rows = result.all()

        spikes = []
        for row in rows:
            daily_avg = row.week_count / 7.0 if row.week_count > 0 else 0
            if daily_avg > 0 and row.today_count > 0:
                ratio = row.today_count / daily_avg
                if ratio > 2.0:
                    spikes.append({
                        "channel_id": str(row.id),
                        "channel_title": row.title,
                        "today_count": row.today_count,
                        "daily_average": round(daily_avg, 1),
                        "ratio": round(ratio, 1),
                    })

        # Sort by ratio descending
        spikes.sort(key=lambda x: x["ratio"], reverse=True)
        return spikes[:10]


# Singleton
insights_service = InsightsService()
