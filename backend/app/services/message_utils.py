"""Message Utility Functions

Shared helper functions for message handling across API endpoints and services.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_

from app.models.message import Message
from app.models.channel import Channel, user_channels
from app.schemas.message import MessageResponse


def message_to_response(message: Message) -> MessageResponse:
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


def apply_message_filters(
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
