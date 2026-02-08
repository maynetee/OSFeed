"""Digest service for building and sending daily digest emails.

Handles message aggregation per collection, LLM-based summarization via Gemini Flash,
and email rendering/sending through the existing email service.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.channel import Channel
from app.models.collection import Collection, collection_channels
from app.models.message import Message
from app.models.user import User
from app.services.email_service import email_service, template_renderer

logger = logging.getLogger(__name__)
settings = get_settings()


def generate_unsubscribe_token(user_id: str) -> str:
    """Generate a JWT token for one-click email unsubscribe (valid 30 days)."""
    payload = {
        "sub": user_id,
        "purpose": "digest_unsubscribe",
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


async def summarize_collection_messages(messages_text: list[str], collection_name: str) -> str:
    """Use Gemini Flash to generate a 3-5 sentence summary of collection messages.

    Falls back to a simple count-based summary if the LLM call fails.
    """
    if not messages_text:
        return "No new messages in this period."

    if not settings.gemini_api_key:
        return f"{len(messages_text)} new messages in {collection_name}."

    combined = "\n---\n".join(messages_text[:30])  # Limit to 30 messages for context window
    prompt = (
        f"You are an OSINT analyst. Summarize the following {len(messages_text)} messages "
        f"from the Telegram collection '{collection_name}' in 3-5 concise sentences. "
        "Focus on key themes, notable events, and actionable intelligence. "
        "Write in English.\n\n"
        f"{combined}"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 300},
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params={"key": settings.gemini_api_key}, json=payload)
            response.raise_for_status()
            data = response.json()

        candidates = data.get("candidates") or []
        if not candidates:
            logger.warning("Gemini summarization returned no candidates")
            return f"{len(messages_text)} new messages in {collection_name}."

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts or "text" not in parts[0]:
            logger.warning("Gemini summarization returned no text")
            return f"{len(messages_text)} new messages in {collection_name}."

        return parts[0]["text"].strip()
    except (httpx.HTTPError, httpx.RequestError, RuntimeError, KeyError) as e:
        logger.error(f"Gemini summarization failed for collection '{collection_name}': {e}")
        return f"{len(messages_text)} new messages in {collection_name}."


async def build_digest_content(
    user: User,
    collection_ids: Optional[list[str]],
    max_messages: int,
    session: AsyncSession,
) -> dict:
    """Build digest content by querying messages, grouping by collection, and generating summaries."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=1)

    # If no collection_ids specified, get all user's collections
    if not collection_ids:
        result = await session.execute(
            select(Collection).where(Collection.user_id == user.id)
        )
        collections = result.scalars().all()
    else:
        result = await session.execute(
            select(Collection).where(Collection.id.in_(collection_ids))
        )
        collections = result.scalars().all()

    digest_collections = []

    for collection in collections:
        # Get channel IDs for this collection
        if collection.is_global:
            ch_result = await session.execute(select(Channel.id).where(Channel.is_active.is_(True)))
            channel_ids = [row.id for row in ch_result.all()]
        else:
            ch_result = await session.execute(
                select(collection_channels.c.channel_id)
                .where(collection_channels.c.collection_id == collection.id)
            )
            channel_ids = [row.channel_id for row in ch_result.all()]

        if not channel_ids:
            continue

        # Query recent messages
        msg_result = await session.execute(
            select(Message)
            .where(Message.channel_id.in_(channel_ids))
            .where(Message.published_at >= since)
            .where(Message.is_duplicate.is_(False))
            .order_by(Message.published_at.desc())
            .limit(max_messages)
        )
        messages = msg_result.scalars().all()

        if not messages:
            continue

        # Build text list for summarization
        messages_text = []
        top_messages = []
        for msg in messages:
            text = msg.translated_text or msg.original_text or ""
            if text.strip():
                messages_text.append(text)
                if len(top_messages) < 5:
                    top_messages.append({
                        "text": text[:300],
                        "published_at": msg.published_at.isoformat() if msg.published_at else "",
                        "id": str(msg.id),
                    })

        summary = await summarize_collection_messages(messages_text, collection.name)

        digest_collections.append({
            "name": collection.name,
            "id": str(collection.id),
            "message_count": len(messages),
            "summary": summary,
            "top_messages": top_messages,
        })

    return {
        "collections": digest_collections,
        "generated_at": now.isoformat(),
        "period": "Last 24 hours",
    }


async def send_digest_email(user: User, content: dict) -> bool:
    """Build and send digest email using the email service."""
    if not settings.email_enabled:
        logger.info(f"Email disabled - would send digest to {user.email}")
        return False

    provider = email_service._get_provider()
    if not provider:
        logger.warning("No email provider configured for digest")
        return False

    unsubscribe_token = generate_unsubscribe_token(str(user.id))
    unsubscribe_url = f"{settings.frontend_url.rstrip('/')}/api/digests/unsubscribe?token={unsubscribe_token}"

    context = {
        "app_name": "OSFeed",
        "user_email": user.email,
        "collections": content["collections"],
        "generated_at": content["generated_at"],
        "period": content["period"],
        "frontend_url": settings.frontend_url.rstrip("/"),
        "unsubscribe_url": unsubscribe_url,
    }

    html = template_renderer.render("daily_digest.html", **context)
    text = template_renderer.render("daily_digest.txt", **context)

    return await provider.send(
        to=user.email,
        subject="Your OSFeed Daily Digest",
        html=html,
        text=text,
    )
