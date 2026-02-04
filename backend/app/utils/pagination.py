"""Pagination utilities for cursor-based pagination."""

import base64
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def encode_cursor(published_at: datetime, message_id: UUID) -> str:
    """Encode a datetime and UUID into a base64 cursor string.

    Args:
        published_at: The datetime to encode
        message_id: The UUID to encode

    Returns:
        Base64-encoded cursor string
    """
    cursor_value = f"{published_at.isoformat()}|{message_id}"
    return base64.urlsafe_b64encode(cursor_value.encode("utf-8")).decode("utf-8")


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    """Decode a base64 cursor string into datetime and UUID.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Tuple of (datetime, UUID)

    Raises:
        HTTPException: If cursor format is invalid
    """
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        published_at_raw, message_id_raw = decoded.split("|", 1)
        published_at = datetime.fromisoformat(published_at_raw)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        message_id = UUID(message_id_raw)
        return published_at, message_id
    except Exception as exc:
        logger.warning(f"Failed to decode cursor: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=400, detail="Invalid cursor format")
