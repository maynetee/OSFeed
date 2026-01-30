"""Redis Event Publishing Service

This module provides functions for publishing events to Redis for real-time updates.
Events are published to the 'osfeed:events' channel for SSE broadcast to frontend clients.
"""

import json
import logging
from uuid import UUID

from app.config import settings

logger = logging.getLogger(__name__)


async def publish_event(event_type: str, data: dict) -> bool:
    """Publish an event to Redis for SSE broadcast.

    Args:
        event_type: Event type identifier (e.g., "message:translated")
        data: Event payload data

    Returns:
        True if event was published successfully, False otherwise
    """
    try:
        from redis.asyncio import Redis

        if not settings.redis_url:
            logger.debug("Redis URL not configured, skipping event publish")
            return False

        redis = Redis.from_url(settings.redis_url, decode_responses=True)

        event_data = {
            "type": event_type,
            "data": data
        }

        await redis.publish("osfeed:events", json.dumps(event_data))
        await redis.close()

        logger.debug(f"Published {event_type} event")
        return True

    except Exception as e:
        logger.error(f"Failed to publish event {event_type}: {e}")
        return False


async def publish_message_translated(
    message_id: UUID,
    channel_id: UUID,
    translated_text: str,
    source_language: str,
    target_language: str
) -> bool:
    """Publish a message translation event to Redis.

    Args:
        message_id: UUID of the translated message
        channel_id: UUID of the channel containing the message
        translated_text: The translated text content
        source_language: Source language code (e.g., "en")
        target_language: Target language code (e.g., "ru")

    Returns:
        True if event was published successfully, False otherwise
    """
    data = {
        "message_id": str(message_id),
        "channel_id": str(channel_id),
        "translated_text": translated_text,
        "source_language": source_language,
        "target_language": target_language
    }

    return await publish_event("message:translated", data)


async def publish_alert_triggered(
    alert_id: UUID,
    channel_id: UUID,
    alert_name: str,
    summary: str,
    match_count: int
) -> bool:
    """Publish an alert triggered event to Redis.

    Args:
        alert_id: UUID of the triggered alert
        channel_id: UUID of the channel where alert was triggered
        alert_name: Name of the triggered alert
        summary: Summary text of matched messages
        match_count: Number of messages that matched the alert

    Returns:
        True if event was published successfully, False otherwise
    """
    data = {
        "alert_id": str(alert_id),
        "channel_id": str(channel_id),
        "alert_name": alert_name,
        "summary": summary,
        "match_count": match_count
    }

    return await publish_event("alert:triggered", data)
