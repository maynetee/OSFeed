import json
import logging
from typing import Literal
from uuid import UUID

from redis.exceptions import RedisError

from app.services.cache import get_redis_client

logger = logging.getLogger(__name__)

EventType = Literal["message:new", "message:update"]

async def publish_message_event(
    event_type: EventType,
    message_ids: list[UUID] | list[str],
    channel_id: UUID | str | None = None,
) -> None:
    """
    Publish a message event to Redis Pub/Sub.
    
    Payload structure:
    {
        "type": event_type,
        "message_ids": [str(id)...],
        "channel_id": str(id) or None
    }
    """
    redis = get_redis_client()
    if not redis:
        logger.warning("Redis not available, skipping publish_message_event")
        return

    payload = {
        "type": event_type,
        "message_ids": [str(mid) for mid in message_ids],
        "channel_id": str(channel_id) if channel_id else None,
    }

    try:
        # We publish to a global channel. Subscribers will filter based on payload.
        await redis.publish("osfeed:events", json.dumps(payload))
        logger.debug(f"Published {event_type} for {len(message_ids)} messages")
    except RedisError as e:
        logger.error(f"Failed to publish message event: {e}")
