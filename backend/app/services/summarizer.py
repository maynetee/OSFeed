from datetime import datetime, timedelta
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
from app.config import get_settings
from app.models.message import Message
from app.models.summary import Summary
from app.models.channel import Channel
from app.models.collection import collection_channels
from app.services.usage import record_api_usage
from typing import Optional, Dict, Any, List
from uuid import UUID
import json
import re

settings = get_settings()


class SummarizerService:
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self._client = None

    @property
    def client(self) -> Optional[AsyncOpenAI]:
        if not self.api_key:
            return None
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key, timeout=60.0)
        return self._client

    def _extract_json(self, content: str) -> Optional[Dict[str, Any]]:
        if not content:
            return None
        fenced_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        if fenced_match:
            try:
                return json.loads(fenced_match.group(1))
            except json.JSONDecodeError:
                return None
        brace_match = re.search(r"(\{.*\})", content, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(1))
            except json.JSONDecodeError:
                return None
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    async def generate_summary(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        if not messages:
            return {
                "title": "Daily Digest",
                "summary": "No messages to summarize.",
                "bullets": [],
                "key_entities": {"persons": [], "locations": [], "organizations": []},
            }

        context_lines = []
        for msg in messages[:60]:
            text = msg["text"].replace("\n", " ").strip()
            context_lines.append(f"[{msg['channel']}]: {text[:500]}")

        context = "\n".join(context_lines)
        target_language = settings.preferred_language

        prompt = (
            "You are an OSINT analyst writing a daily digest. "
            "Return ONLY valid JSON with keys: "
            "title (string), summary (string), bullets (array of strings), "
            "key_entities (object with persons/locations/organizations arrays). "
            f"Output language: {target_language}. "
            "Keep the summary factual and concise, and the bullets actionable.\n\n"
            f"Messages:\n{context}"
        )

        client = self.client
        if client is None:
            return {
                "title": "Daily Digest",
                "summary": "\n".join([msg["text"] for msg in messages[:10]]),
                "bullets": [],
                "key_entities": {"persons": [], "locations": [], "organizations": []},
            }

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You format responses as strict JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            content = response.choices[0].message.content.strip()
            if response.usage:
                await record_api_usage(
                    provider="openai",
                    model=self.model,
                    purpose="summary",
                    prompt_tokens=response.usage.prompt_tokens or 0,
                    completion_tokens=response.usage.completion_tokens or 0,
                    metadata={"message_count": len(messages)},
                )
            data = self._extract_json(content)
            if not data:
                raise ValueError("Failed to parse summary JSON")
            return data
        except Exception as e:
            print(f"Summary generation failed: {e}")
            return {
                "title": "Daily Digest",
                "summary": "Failed to generate summary.",
                "bullets": [],
                "key_entities": {"persons": [], "locations": [], "organizations": []},
            }


def _build_digest_html(
    title: str,
    summary: str,
    bullets: List[str],
    entities: Dict[str, List[str]],
) -> str:
    bullet_items = "".join([f"<li>{item}</li>" for item in bullets])
    entity_section = ""
    if entities:
        entity_section = (
            "<h3>Key Entities</h3>"
            "<div class=\"entities\">"
            f"<p><strong>Persons:</strong> {', '.join(entities.get('persons', [])) or 'None'}</p>"
            f"<p><strong>Locations:</strong> {', '.join(entities.get('locations', [])) or 'None'}</p>"
            f"<p><strong>Organizations:</strong> {', '.join(entities.get('organizations', [])) or 'None'}</p>"
            "</div>"
        )

    return f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #1f2933; line-height: 1.5;">
    <h2>{title}</h2>
    <p>{summary}</p>
    {'<h3>Highlights</h3><ul>' + bullet_items + '</ul>' if bullets else ''}
    {entity_section}
  </body>
</html>
""".strip()


def _apply_summary_filters(query, filters: Optional[Dict[str, Any]]):
    if not filters:
        return query

    collections = filters.get("collections") or []
    languages = filters.get("languages") or []
    keywords = filters.get("keywords") or []

    if collections:
        query = query.join(
            collection_channels,
            collection_channels.c.channel_id == Channel.id,
        ).where(collection_channels.c.collection_id.in_(collections))

    if languages:
        query = query.where(Message.source_language.in_(languages))

    if keywords:
        keyword_filters = []
        for keyword in keywords:
            like_pattern = f"%{keyword}%"
            keyword_filters.append(Message.translated_text.ilike(like_pattern))
            keyword_filters.append(Message.original_text.ilike(like_pattern))
        query = query.where(or_(*keyword_filters))

    return query


async def generate_daily_summary(
    db: AsyncSession = None,
    user_id: Optional[UUID] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> Summary:
    """
    Generate daily summary for the last 24 hours.

    IMPORTANT: This function releases the database lock during the LLM API call
    to prevent blocking other database operations. It uses short-lived sessions
    for reading and writing data.

    Args:
        db: Deprecated, no longer used. Kept for backward compatibility.

    Returns:
        Created Summary object
    """
    from app.database import AsyncSessionLocal

    # Step 1: Get messages from last 24 hours (short DB session)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=1)

    async with AsyncSessionLocal() as session:
        base_query = (
            select(Message, Channel)
            .join(Channel)
            .where(Message.published_at >= start_time)
            .where(Message.published_at <= end_time)
        )
        base_query = _apply_summary_filters(base_query, filters)

        result = await session.execute(
            base_query.where(Message.is_duplicate == False)
        )
        rows = result.all()

        duplicates_query = (
            select(func.count())
            .select_from(Message)
            .join(Channel)
            .where(Message.published_at >= start_time)
            .where(Message.published_at <= end_time)
            .where(Message.is_duplicate == True)
        )
        duplicates_query = _apply_summary_filters(duplicates_query, filters)
        duplicates_result = await session.execute(duplicates_query)
        duplicates_filtered = duplicates_result.scalar() or 0

        # Prepare messages for summarization (extract data before closing session)
        messages_data = [
            {
                'text': msg.translated_text or msg.original_text or "",
                'channel': channel.title
            }
            for msg, channel in rows
        ]
        channels_covered = len({channel.id for _, channel in rows})
        extracted_entities = {"persons": set(), "locations": set(), "organizations": set()}
        for msg, _ in rows:
            if msg.entities:
                extracted_entities["persons"].update(msg.entities.get("persons", []))
                extracted_entities["locations"].update(msg.entities.get("locations", []))
                extracted_entities["organizations"].update(msg.entities.get("organizations", []))

    # Step 2: Generate summary via LLM API (NO DB session held - this is slow)
    summarizer = SummarizerService()
    summary_data = await summarizer.generate_summary(messages_data)
    summary_title = summary_data.get("title") or "Daily Digest"
    summary_content = summary_data.get("summary") or "No summary generated."
    summary_bullets = summary_data.get("bullets") or []
    summary_entities = summary_data.get("key_entities") or {}
    for key in ("persons", "locations", "organizations"):
        existing = set(summary_entities.get(key, []))
        existing.update(extracted_entities.get(key, set()))
        summary_entities[key] = sorted(existing)
    summary_html = _build_digest_html(summary_title, summary_content, summary_bullets, summary_entities)

    # Step 3: Save summary to DB (short DB session)
    async with AsyncSessionLocal() as session:
        summary = Summary(
            digest_type='daily',
            title=summary_title,
            content=summary_content,
            content_html=summary_html,
            entities=summary_entities,
            message_count=len(messages_data),
            channels_covered=channels_covered,
            duplicates_filtered=duplicates_filtered,
            period_start=start_time,
            period_end=end_time,
            user_id=user_id,
            filters=filters or {"collections": [], "languages": [], "keywords": []},
        )

        session.add(summary)
        await session.commit()
        await session.refresh(summary)

        return summary
