"""Message Export Service

This module provides functions for exporting messages in various formats (CSV, HTML, PDF).
"""

import csv
import html
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


async def export_messages_html(
    user_id: UUID,
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> AsyncGenerator[str, None]:
    """Export messages to HTML format.

    Args:
        user_id: UUID of the user requesting the export
        channel_id: Optional single channel ID to filter by
        channel_ids: Optional list of channel IDs to filter by
        start_date: Optional start date for filtering messages
        end_date: Optional end date for filtering messages

    Yields:
        HTML data chunks as strings
    """
    # Write HTML header and table start
    html_header = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Message Export</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .duplicate {
            color: #ff9800;
        }
    </style>
</head>
<body>
    <h1>Message Export</h1>
    <table>
        <thead>
            <tr>
                <th>Message ID</th>
                <th>Channel</th>
                <th>Username</th>
                <th>Published At</th>
                <th>Original Text</th>
                <th>Translated Text</th>
                <th>Source Lang</th>
                <th>Target Lang</th>
                <th>Duplicate</th>
            </tr>
        </thead>
        <tbody>
"""
    yield html_header

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

            output = StringIO()
            for message, channel in rows:
                duplicate_class = ' class="duplicate"' if message.is_duplicate else ''
                output.write(f"            <tr{duplicate_class}>\n")
                output.write(f"                <td>{html.escape(str(message.id))}</td>\n")
                output.write(f"                <td>{html.escape(channel.title or '')}</td>\n")
                output.write(f"                <td>{html.escape(channel.username or '')}</td>\n")
                output.write(f"                <td>{html.escape(str(message.published_at))}</td>\n")
                output.write(f"                <td>{html.escape(message.original_text or '')}</td>\n")
                output.write(f"                <td>{html.escape(message.translated_text or '')}</td>\n")
                output.write(f"                <td>{html.escape(message.source_language or '')}</td>\n")
                output.write(f"                <td>{html.escape(message.target_language or '')}</td>\n")
                output.write(f"                <td>{html.escape(str(message.is_duplicate))}</td>\n")
                output.write("            </tr>\n")

            data = output.getvalue()
            if data:
                yield data

            offset += len(rows)
            if len(rows) < batch_size:
                break

    # Write HTML footer
    html_footer = """        </tbody>
    </table>
</body>
</html>
"""
    yield html_footer
