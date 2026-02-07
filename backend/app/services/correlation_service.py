"""Cross-Source Correlation Service — analyzes duplicate message groups from multiple sources."""

import json
import logging
from uuid import UUID

import httpx
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.analysis import Correlation
from app.models.message import Message
from app.services.usage import record_api_usage

logger = logging.getLogger(__name__)
settings = get_settings()

MAX_GROUPS_PER_RUN = 5
MIN_SOURCES = 3


class CorrelationService:
    async def analyze_duplicate_group(self, duplicate_group_id: UUID, messages: list[dict]) -> dict:
        """Analyze a group of messages from different sources about the same event."""
        messages_text = "\n\n".join(
            f"[Source: {m['channel_title']}] {m['text']}" for m in messages
        )

        prompt = (
            "These messages from different Telegram channels describe the same event. "
            "Compare their accounts and return ONLY valid JSON with these keys:\n"
            '- "consistent_facts": list of facts reported by multiple sources\n'
            '- "unique_details": list of details only reported by specific sources '
            "(include which source)\n"
            '- "contradictions": list of conflicting information between sources\n'
            '- "analysis": brief overall assessment of source agreement\n\n'
            f"Messages:\n{messages_text}"
        )

        if not settings.gemini_api_key:
            logger.warning("Gemini API key not configured, skipping correlation analysis")
            return {
                "consistent_facts": [],
                "unique_details": [],
                "contradictions": [],
                "analysis_text": "Analysis unavailable — no LLM API key configured.",
            }

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent"
        )
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3},
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url, params={"key": settings.gemini_api_key}, json=payload
            )
            response.raise_for_status()
            data = response.json()

        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini correlation analysis returned no candidates")
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts or "text" not in parts[0]:
            raise RuntimeError("Gemini correlation analysis returned no text")

        raw_text = parts[0]["text"].strip()

        # Record API usage
        usage_meta = data.get("usageMetadata", {})
        await record_api_usage(
            provider="gemini",
            model=settings.gemini_model,
            purpose="correlation_analysis",
            prompt_tokens=usage_meta.get("promptTokenCount", 0),
            completion_tokens=usage_meta.get("candidatesTokenCount", 0),
            metadata={"duplicate_group_id": str(duplicate_group_id), "source_count": len(messages)},
        )

        # Parse JSON from response (handle markdown code fences)
        json_text = raw_text
        if "```json" in json_text:
            json_text = json_text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in json_text:
            json_text = json_text.split("```", 1)[1].split("```", 1)[0]

        try:
            result = json.loads(json_text.strip())
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse LLM JSON for group {duplicate_group_id}, using raw text")
            return {
                "consistent_facts": [],
                "unique_details": [],
                "contradictions": [],
                "analysis_text": raw_text,
            }

        return {
            "consistent_facts": result.get("consistent_facts", []),
            "unique_details": result.get("unique_details", []),
            "contradictions": result.get("contradictions", []),
            "analysis_text": result.get("analysis", ""),
        }

    async def process_new_correlations(self):
        """Find duplicate groups with 3+ sources that don't have correlations yet."""
        async with AsyncSessionLocal() as db:
            # Find groups with enough distinct sources
            group_query = (
                select(
                    Message.duplicate_group_id,
                    func.count(distinct(Message.channel_id)).label("source_count"),
                )
                .where(Message.duplicate_group_id.isnot(None))
                .group_by(Message.duplicate_group_id)
                .having(func.count(distinct(Message.channel_id)) >= MIN_SOURCES)
            )

            # Exclude already-processed groups
            existing = select(Correlation.duplicate_group_id)
            group_query = group_query.where(Message.duplicate_group_id.notin_(existing))

            result = await db.execute(group_query.limit(MAX_GROUPS_PER_RUN))
            groups = result.all()

            if not groups:
                return

            logger.info(f"Processing {len(groups)} new correlation groups")

            for group_id, source_count in groups:
                try:
                    await self._process_group(db, group_id, source_count)
                except Exception:
                    logger.exception(f"Failed to process correlation for group {group_id}")

    async def _process_group(self, db: AsyncSession, group_id: UUID, source_count: int):
        """Process a single duplicate group: fetch messages, run LLM, store result."""
        msg_query = (
            select(Message)
            .where(Message.duplicate_group_id == group_id)
            .order_by(Message.published_at)
        )
        result = await db.execute(msg_query)
        messages = result.scalars().all()

        if not messages:
            return

        # Build message dicts for LLM
        msg_dicts = []
        for m in messages:
            channel = await db.run_sync(lambda session: m.channel)
            channel_title = channel.title if channel else "Unknown"
            msg_dicts.append({
                "channel_title": channel_title,
                "text": m.translated_text or m.original_text or "",
            })

        analysis = await self.analyze_duplicate_group(group_id, msg_dicts)

        correlation = Correlation(
            duplicate_group_id=group_id,
            analysis_text=analysis["analysis_text"],
            consistent_facts=analysis["consistent_facts"],
            unique_details=analysis["unique_details"],
            contradictions=analysis["contradictions"],
            source_count=source_count,
        )
        db.add(correlation)
        await db.commit()
        logger.info(f"Created correlation for group {group_id} ({source_count} sources)")


correlation_service = CorrelationService()
