"""Message Export Service

This module provides functions for exporting messages in various formats (CSV, HTML, PDF).
"""

import asyncio
import logging
from datetime import datetime
from io import StringIO
from typing import Optional, AsyncGenerator
from uuid import UUID

from sqlalchemy import select, desc

from app.database import AsyncSessionLocal
from app.models.message import Message
from app.models.channel import Channel
from app.services.message_utils import apply_message_filters as _apply_message_filters
from app.utils.export import (
    MESSAGE_CSV_COLUMNS,
    create_csv_writer,
    generate_csv_row,
    generate_html_template,
    generate_html_article,
    generate_pdf_bytes,
)

logger = logging.getLogger(__name__)


async def export_messages_csv(
    user_id: UUID,
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    media_types: Optional[list[str]] = None,
) -> AsyncGenerator[str, None]:
    """Export messages to CSV format.

    Args:
        user_id: UUID of the user requesting the export
        channel_id: Optional single channel ID to filter by
        channel_ids: Optional list of channel IDs to filter by
        start_date: Optional start date for filtering messages
        end_date: Optional end date for filtering messages
        media_types: Optional list of media types to filter by

    Yields:
        CSV data chunks as strings
    """
    writer, output = create_csv_writer()

    # Write CSV header
    writer.writerow(MESSAGE_CSV_COLUMNS)
    yield output.getvalue()
    output.seek(0)
    output.truncate(0)

    batch_size = 500
    offset = 0

    while True:
        async with AsyncSessionLocal() as db:
            query = select(Message, Channel).join(Channel)
            query = _apply_message_filters(query, user_id, channel_id, channel_ids, start_date, end_date, media_types)
            query = query.order_by(desc(Message.published_at))
            query = query.limit(batch_size).offset(offset)

            result = await db.execute(query)
            rows = result.all()

            if not rows:
                break

            for message, channel in rows:
                writer.writerow(generate_csv_row(message, channel))

            data = output.getvalue()
            if data:
                yield data
                output.seek(0)
                output.truncate(0)

            offset += len(rows)
            if len(rows) < batch_size:
                break


async def export_messages_html(
    user_id: UUID,
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 200,
    media_types: Optional[list[str]] = None,
) -> AsyncGenerator[str, None]:
    """Export messages to HTML format.

    Args:
        user_id: UUID of the user requesting the export
        channel_id: Optional single channel ID to filter by
        channel_ids: Optional list of channel IDs to filter by
        start_date: Optional start date for filtering messages
        end_date: Optional end date for filtering messages
        limit: Maximum number of messages to export (default: 200)
        media_types: Optional list of media types to filter by

    Yields:
        HTML data chunks as strings
    """
    yield generate_html_template("OSFeed - Messages")
    yield "<h1>Export messages</h1>"

    batch_size = 100
    offset = 0
    processed = 0

    while processed < limit:
        curr_limit = min(batch_size, limit - processed)

        async with AsyncSessionLocal() as db:
            query = select(Message, Channel).join(Channel)
            query = _apply_message_filters(query, user_id, channel_id, channel_ids, start_date, end_date, media_types)
            query = query.order_by(desc(Message.published_at))
            query = query.limit(curr_limit).offset(offset)
            result = await db.execute(query)
            rows = result.all()

        if not rows:
            break

        chunk = []
        for message, channel in rows:
            chunk.append(generate_html_article(message, channel))

        yield "".join(chunk)

        count = len(rows)
        processed += count
        offset += count

        if count < curr_limit:
            break

    yield "</body></html>"


async def export_messages_pdf(
    user_id: UUID,
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 1000,
    media_types: Optional[list[str]] = None,
) -> bytes:
    """Export messages to PDF format.

    Args:
        user_id: UUID of the user requesting the export
        channel_id: Optional single channel ID to filter by
        channel_ids: Optional list of channel IDs to filter by
        start_date: Optional start date for filtering messages
        end_date: Optional end date for filtering messages
        limit: Maximum number of messages to export (default: 1000)
        media_types: Optional list of media types to filter by

    Returns:
        PDF file content as bytes
    """
    async with AsyncSessionLocal() as db:
        query = select(Message, Channel).join(Channel)
        query = _apply_message_filters(query, user_id, channel_id, channel_ids, start_date, end_date, media_types)
        query = query.order_by(desc(Message.published_at))
        query = query.limit(limit)
        result = await db.execute(query)
        rows = result.all()

    data = []
    for message, channel in rows:
        data.append({
            "channel_title": channel.title,
            "channel_username": channel.username,
            "published_at": message.published_at,
            "translated_text": message.translated_text,
            "original_text": message.original_text,
        })

    if not data:
        return b""

    pdf_bytes = await asyncio.to_thread(generate_pdf_bytes, data)
    return pdf_bytes
