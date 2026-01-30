"""Export utilities for CSV, HTML, and PDF generation."""
import csv
from io import StringIO
from typing import Any, Optional


# Standard CSV columns for message exports
MESSAGE_CSV_COLUMNS = [
    "message_id",
    "channel_title",
    "channel_username",
    "published_at",
    "original_text",
    "translated_text",
    "source_language",
    "target_language",
    "is_duplicate",
]


def create_csv_writer(output: Optional[StringIO] = None) -> tuple[csv.writer, StringIO]:
    """Create a CSV writer with a StringIO buffer.

    Args:
        output: Optional StringIO buffer. If None, a new one is created.

    Returns:
        tuple: (csv.writer, StringIO) - The writer and its buffer.
    """
    if output is None:
        output = StringIO()
    writer = csv.writer(output)
    return writer, output


def generate_csv_row(message: Any, channel: Any) -> list:
    """Generate a standard CSV row for a message.

    Args:
        message: Message object with attributes: id, published_at, original_text,
                 translated_text, source_language, target_language, is_duplicate
        channel: Channel object with attributes: title, username

    Returns:
        list: Row data ready for csv.writer.writerow()
    """
    return [
        str(message.id),
        channel.title,
        channel.username,
        message.published_at,
        message.original_text or "",
        message.translated_text or "",
        message.source_language or "",
        message.target_language or "",
        message.is_duplicate,
    ]
