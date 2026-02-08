"""Message Streaming Service

This module provides Server-Sent Events (SSE) streaming functionality for messages.
It handles both historical message batching and real-time updates via Redis Pub/Sub.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional
from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError
from sqlalchemy import desc, select, tuple_
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.message import Message
from app.services.message_utils import (
    apply_message_filters as _apply_message_filters,
)
from app.services.message_utils import (
    message_to_response as _message_to_response,
)

logger = logging.getLogger(__name__)


async def create_message_stream(
    user_id: UUID,
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    batch_size: int = 20,
    limit: int = 200,
    realtime: bool = False,
    media_types: Optional[list[str]] = None,
) -> AsyncGenerator[str, None]:
    """Create an SSE message stream with historical batching and optional real-time updates.

    This function yields Server-Sent Events formatted strings for streaming messages to clients.
    It first streams historical messages in batches, then optionally tails for real-time updates
    via Redis Pub/Sub.

    Args:
        user_id: User ID for permission filtering
        channel_id: Optional single channel filter
        channel_ids: Optional multiple channel filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        batch_size: Number of messages per batch (1-100)
        limit: Maximum total messages to stream (1-1000)
        realtime: Whether to tail for real-time updates after historical messages
        media_types: Optional media types filter

    Yields:
        SSE-formatted strings with message data, errors, or connection events

    Example:
        async for event in create_message_stream(user_id=uuid, realtime=True):
            # event is a string like: "data: {...}\n\n"
            pass
    """
    offset = 0
    sent = 0
    last_published_at = None
    last_message_id = None

    # 1. Stream historical messages - reuse a single DB session for all batches
    async with AsyncSessionLocal() as db:
        while sent < limit:
            current_batch = min(batch_size, limit - sent)
            query = select(Message).options(selectinload(Message.channel))
            query = _apply_message_filters(query, user_id, channel_id, channel_ids, start_date, end_date, media_types)
            query = query.order_by(desc(Message.published_at), desc(Message.id))
            query = query.limit(current_batch).offset(offset)
            result = await db.execute(query)
            messages = result.scalars().all()

            if not messages:
                break

            if offset == 0 and messages:
                newest = messages[0]
                last_published_at = newest.published_at
                last_message_id = newest.id

            payload = {
                "messages": [
                    _message_to_response(message).model_dump(mode="json")
                    for message in messages
                ],
                "offset": offset,
                "count": len(messages),
                "type": "history"
            }
            yield f"data: {json.dumps(payload)}\n\n"

            offset += len(messages)
            sent += len(messages)
            await asyncio.sleep(0)

    # 2. Realtime tailing via Redis Pub/Sub
    if realtime:
        settings = get_settings()
        if not settings.redis_url:
            yield "event: error\ndata: {\"error\": \"Realtime unavailable\"}\n\n"
            return

        # Dedicated Redis client for pub/sub with no socket_timeout
        # (the shared client has socket_timeout=5 which kills long-lived subscriptions)
        pubsub_redis = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=10,
            socket_timeout=None,  # No timeout for blocking pub/sub reads
            socket_keepalive=True,
            health_check_interval=30,
        )
        pubsub = pubsub_redis.pubsub()
        await pubsub.subscribe("osfeed:events")
        yield "event: connected\ndata: {}\n\n"

        if not last_published_at:
            last_published_at = datetime.now(timezone.utc)

        try:
            while True:
                try:
                    async for event in pubsub.listen():
                        if event["type"] != "message":
                            continue

                        data = json.loads(event["data"])
                        event_type = data.get("type", "")

                        # Handle translation events - forward directly to client
                        if event_type == "message:translated":
                            translation_event = {
                                "type": "message:translated",
                                "data": data.get("data", {})
                            }
                            yield f"data: {json.dumps(translation_event)}\n\n"
                            continue

                        # Handle alert events - forward directly to client
                        if event_type == "alert:triggered":
                            alert_event = {
                                "type": "alert:triggered",
                                "data": data.get("data", {})
                            }
                            yield f"data: {json.dumps(alert_event)}\n\n"
                            continue

                        # Handle new message events - query DB and send
                        if event_type == "message:new":
                            async with AsyncSessionLocal() as db:
                                query = select(Message).options(selectinload(Message.channel))
                                query = _apply_message_filters(
                                    query, user_id, channel_id, channel_ids, None, None, media_types,
                                )

                                if last_message_id:
                                    query = query.where(
                                        tuple_(Message.published_at, Message.id) > (last_published_at, last_message_id)
                                    )
                                else:
                                    query = query.where(Message.published_at > last_published_at)

                                query = query.order_by(Message.published_at.asc(), Message.id.asc())
                                query = query.limit(50)

                                result = await db.execute(query)
                                new_messages = result.scalars().all()

                            if new_messages:
                                newest = new_messages[-1]
                                last_published_at = newest.published_at
                                last_message_id = newest.id

                                payload = {
                                    "messages": [
                                        _message_to_response(msg).model_dump(mode="json")
                                        for msg in new_messages
                                    ],
                                    "type": "realtime"
                                }
                                yield f"data: {json.dumps(payload)}\n\n"
                except (RedisTimeoutError, RedisConnectionError, OSError) as e:
                    logger.warning(f"Redis pub/sub connection lost: {type(e).__name__}: {e}, reconnecting...")
                    try:
                        await pubsub.unsubscribe("osfeed:events")
                    except Exception:
                        pass
                    await asyncio.sleep(2)
                    try:
                        await pubsub.subscribe("osfeed:events")
                    except Exception:
                        # If resubscribe fails, recreate the pub/sub object
                        try:
                            await pubsub.close()
                        except Exception:
                            pass
                        pubsub = pubsub_redis.pubsub()
                        await pubsub.subscribe("osfeed:events")
                    continue
        except asyncio.CancelledError:
            pass
        finally:
            try:
                await pubsub.unsubscribe("osfeed:events")
                await pubsub.close()
            except Exception:
                pass
            await pubsub_redis.close()

    yield "event: end\ndata: {}\n\n"
