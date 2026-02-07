"""Timeline Reconstruction Service - Generates chronological event timelines from intelligence messages."""

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.analysis import Timeline
from app.models.channel import Channel
from app.models.collection import collection_channels
from app.models.message import Message

settings = get_settings()
logger = logging.getLogger(__name__)


class TimelineService:
    async def generate_timeline(
        self,
        user_id: UUID,
        topic: Optional[str],
        collection_id: Optional[UUID],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        db: AsyncSession = None,
    ):
        """Generate a timeline from intelligence messages."""
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=7)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        if topic:
            messages = await self._fetch_messages_by_topic(topic, start_date, end_date, db)
        elif collection_id:
            messages = await self._fetch_messages_by_collection(collection_id, start_date, end_date, db)
        else:
            return None

        if not messages:
            timeline = Timeline(
                id=uuid.uuid4(),
                user_id=user_id,
                title=f"Timeline: {topic or 'Collection'}",
                topic=topic,
                collection_id=collection_id,
                events=[],
                date_range_start=start_date,
                date_range_end=end_date,
                message_count=0,
            )
            db.add(timeline)
            await db.commit()
            await db.refresh(timeline)
            return timeline

        messages_text = self._format_messages(messages)
        events = await self._call_gemini_timeline(messages_text)

        title = f"Timeline: {topic}" if topic else f"Timeline: Collection analysis"
        timeline = Timeline(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title,
            topic=topic,
            collection_id=collection_id,
            events=events,
            date_range_start=start_date,
            date_range_end=end_date,
            message_count=len(messages),
        )
        db.add(timeline)
        await db.commit()
        await db.refresh(timeline)
        return timeline

    async def _fetch_messages_by_topic(self, topic: str, start_date, end_date, db: AsyncSession):
        """Fetch messages matching a topic keyword."""
        pattern = f"%{topic}%"
        query = (
            select(Message, Channel.title.label("channel_title"))
            .join(Channel, Channel.id == Message.channel_id)
            .where(
                Message.published_at >= start_date,
                Message.published_at <= end_date,
                or_(
                    Message.original_text.ilike(pattern),
                    Message.translated_text.ilike(pattern),
                ),
            )
            .order_by(Message.published_at)
            .limit(100)
        )
        result = await db.execute(query)
        return result.all()

    async def _fetch_messages_by_collection(self, collection_id: UUID, start_date, end_date, db: AsyncSession):
        """Fetch messages from a collection's channels."""
        query = (
            select(Message, Channel.title.label("channel_title"))
            .join(Channel, Channel.id == Message.channel_id)
            .join(collection_channels, collection_channels.c.channel_id == Channel.id)
            .where(
                collection_channels.c.collection_id == collection_id,
                Message.published_at >= start_date,
                Message.published_at <= end_date,
            )
            .order_by(Message.published_at)
            .limit(100)
        )
        result = await db.execute(query)
        return result.all()

    def _format_messages(self, messages) -> str:
        """Format messages into text for LLM processing."""
        lines = []
        for row in messages:
            msg = row[0] if hasattr(row, '__getitem__') else row.Message
            channel_title = row[1] if hasattr(row, '__getitem__') else row.channel_title
            text = msg.translated_text or msg.original_text or ""
            date_str = msg.published_at.strftime("%Y-%m-%d %H:%M") if msg.published_at else "unknown"
            lines.append(f"[{date_str}] [{channel_title}] {text[:500]}")
        return "\n".join(lines)

    async def _call_gemini_timeline(self, messages_text: str) -> list[dict]:
        """Call Gemini to reconstruct timeline from messages."""
        if not settings.gemini_api_key:
            logger.warning("Gemini API key not configured, returning empty timeline")
            return []

        prompt = (
            "You are an OSINT analyst. Reconstruct a timeline of events from these intelligence messages.\n"
            "For each distinct event, provide:\n"
            "- date: ISO date string\n"
            "- description: concise description of what happened\n"
            "- sources: list of channel names that reported this\n"
            "- significance: 1-5 scale (5 = major event)\n\n"
            "Group related messages into single events. Order chronologically.\n"
            "Return ONLY valid JSON array: "
            '[{"date": "...", "description": "...", "sources": [...], "significance": N}]\n\n'
            f"Messages:\n{messages_text}"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3},
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, params={"key": settings.gemini_api_key}, json=payload)
                response.raise_for_status()
                data = response.json()

            candidates = data.get("candidates") or []
            if not candidates:
                logger.error("Gemini timeline returned no candidates")
                return []

            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            # Strip markdown code fences if present
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            events = json.loads(text)
            if not isinstance(events, list):
                logger.error("Gemini timeline did not return a list")
                return []
            return events
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Timeline generation failed: {e}")
            return []


timeline_service = TimelineService()
