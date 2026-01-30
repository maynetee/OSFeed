"""Message Streaming Service

This module provides Server-Sent Events (SSE) streaming functionality for messages.
It handles both historical message batching and real-time updates via Redis Pub/Sub.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, AsyncGenerator
from uuid import UUID

from sqlalchemy import select, desc, tuple_, and_
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.message import Message
from app.models.channel import Channel, user_channels
from app.schemas.message import MessageResponse
from app.services.cache import get_redis_client

logger = logging.getLogger(__name__)


def _message_to_response(message: Message) -> MessageResponse:
    """Convert Message model to MessageResponse schema.

    Args:
        message: Message model instance with optional channel relationship

    Returns:
        MessageResponse schema with channel details if available
    """
    data = MessageResponse.model_validate(message).model_dump()
    if message.channel:
        data["channel_title"] = message.channel.title
        data["channel_username"] = message.channel.username
    return MessageResponse(**data)


def _apply_message_filters(
    query,
    user_id: UUID,
    channel_id: Optional[UUID],
    channel_ids: Optional[list[UUID]],
    start_date: Optional[datetime],
    end_date: Optional[datetime],
):
    """Apply filters to message query based on user permissions and optional filters.

    Args:
        query: SQLAlchemy query to filter
        user_id: User ID for permission filtering
        channel_id: Optional single channel filter
        channel_ids: Optional multiple channel filter
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        Filtered SQLAlchemy query
    """
    query = query.join(Channel, Message.channel_id == Channel.id).join(
        user_channels,
        and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user_id)
    )

    if channel_ids:
        query = query.where(Message.channel_id.in_(channel_ids))
    elif channel_id:
        query = query.where(Message.channel_id == channel_id)

    if start_date:
        query = query.where(Message.published_at >= start_date)

    if end_date:
        query = query.where(Message.published_at <= end_date)

    return query


async def create_message_stream(
    user_id: UUID,
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    batch_size: int = 20,
    limit: int = 200,
    realtime: bool = False,
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
            query = _apply_message_filters(query, user_id, channel_id, channel_ids, start_date, end_date)
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
        redis = get_redis_client()
        if not redis:
            # Fallback to polling if Redis is down
            yield "event: error\ndata: {\"error\": \"Realtime unavailable\"}\n\n"
            return

        pubsub = redis.pubsub()
        await pubsub.subscribe("osfeed:events")
        yield "event: connected\ndata: {}\n\n"

        if not last_published_at:
            last_published_at = datetime.now(timezone.utc)

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

                # Handle new message events - query DB and send
                if event_type == "message:new":
                    async with AsyncSessionLocal() as db:
                        query = select(Message).options(selectinload(Message.channel))
                        query = _apply_message_filters(query, user_id, channel_id, channel_ids, None, None)

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
        except asyncio.CancelledError:
            await pubsub.unsubscribe("osfeed:events")
            raise

    yield "event: end\ndata: {}\n\n"
