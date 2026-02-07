"""Message Utility Functions

Shared helper functions for message handling across API endpoints and services.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, or_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
    media_types: Optional[list[str]] = None,
    region: Optional[str] = None,
):
    """Apply filters to message query based on user permissions and optional filters.

    Args:
        query: SQLAlchemy query to filter
        user_id: User ID for permission filtering
        channel_id: Optional single channel filter
        channel_ids: Optional multiple channel filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        media_types: Optional media types filter
        region: Optional channel region filter

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

    if media_types:
        # Handle "text" filter specially - it means messages with no media
        if "text" in media_types:
            # If text is the only filter, show only text messages
            if len(media_types) == 1:
                query = query.where(Message.media_type.is_(None))
            else:
                # If text + other types, show text OR the other media types
                other_types = [mt for mt in media_types if mt != "text"]
                query = query.where(
                    or_(Message.media_type.is_(None), Message.media_type.in_(other_types))
                )
        else:
            # Only non-text media types selected
            query = query.where(Message.media_type.in_(media_types))

    if region:
        query = query.where(Channel.region == region)

    return query


async def get_single_message(
    message_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> Optional[Message]:
    """Get a single message by ID with user authorization.

    Args:
        message_id: ID of the message
        user_id: User ID for permission filtering
        db: Database session

    Returns:
        Message if found and user has access, None otherwise
    """
    result = await db.execute(
        select(Message)
        .options(selectinload(Message.channel))
        .join(Channel, Message.channel_id == Channel.id)
        .join(
            user_channels,
            and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user_id),
        )
        .where(Message.id == message_id)
    )
    return result.scalar_one_or_none()


async def get_similar_messages(
    message_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> tuple[list[Message], Optional[str]]:
    """Get similar messages based on duplicate_group_id.

    Args:
        message_id: ID of the source message
        user_id: User ID for permission filtering
        db: Database session

    Returns:
        Tuple of (list of similar messages, duplicate_group_id)
        Returns ([], None) if source message not found or has no duplicate_group_id
    """
    # Get the source message to find its duplicate_group_id
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    source_message = result.scalar_one_or_none()

    if not source_message or not source_message.duplicate_group_id:
        return ([], None)

    # Query for similar messages with user authorization
    query = (
        select(Message)
        .options(selectinload(Message.channel))
        .join(Channel, Message.channel_id == Channel.id)
        .join(
            user_channels,
            and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user_id)
        )
        .where(
            and_(
                Message.duplicate_group_id == source_message.duplicate_group_id,
                Message.id != message_id
            )
        )
        .order_by(desc(Message.published_at), desc(Message.id))
    )

    result = await db.execute(query)
    messages = result.scalars().all()

    return (list(messages), source_message.duplicate_group_id)
