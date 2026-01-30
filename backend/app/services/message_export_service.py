"""Message Export Service

This module provides functions for exporting messages in various formats (CSV, HTML, PDF).
"""

import csv
import logging
from datetime import datetime
from io import StringIO
from typing import Optional, AsyncGenerator
from uuid import UUID

from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.message import Message
from app.models.channel import Channel, user_channels

logger = logging.getLogger(__name__)


def _apply_message_filters(
    query,
    user_id: UUID,
    channel_id: Optional[UUID],
    channel_ids: Optional[list[UUID]],
    start_date: Optional[datetime],
    end_date: Optional[datetime],
):
    """Apply filters to message query for user access control and date ranges."""
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


async def export_messages_csv(
    user_id: UUID,
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> AsyncGenerator[str, None]:
    """Export messages to CSV format.

    Args:
        user_id: UUID of the user requesting the export
        channel_id: Optional single channel ID to filter by
        channel_ids: Optional list of channel IDs to filter by
        start_date: Optional start date for filtering messages
        end_date: Optional end date for filtering messages

    Yields:
        CSV data chunks as strings
    """
    output = StringIO()
    writer = csv.writer(output)

    # Write CSV header
    writer.writerow([
        "message_id", "channel_title", "channel_username", "published_at",
        "original_text", "translated_text", "source_language",
        "target_language", "is_duplicate"
    ])
    yield output.getvalue()
    output.seek(0)
    output.truncate(0)

    batch_size = 500
    offset = 0

    while True:
        async with AsyncSessionLocal() as db:
            query = select(Message, Channel).join(Channel)
            query = _apply_message_filters(query, user_id, channel_id, channel_ids, start_date, end_date)
            query = query.order_by(desc(Message.published_at))
            query = query.limit(batch_size).offset(offset)

            result = await db.execute(query)
            rows = result.all()

            if not rows:
                break

            for message, channel in rows:
                writer.writerow([
                    str(message.id),
                    channel.title,
                    channel.username,
                    message.published_at,
                    message.original_text or "",
                    message.translated_text or "",
                    message.source_language or "",
                    message.target_language or "",
                    message.is_duplicate,
                ])

            data = output.getvalue()
            if data:
                yield data
                output.seek(0)
                output.truncate(0)

            offset += len(rows)
            if len(rows) < batch_size:
                break
