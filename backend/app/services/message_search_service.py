"""Message Search Service

This module provides functions for building search queries with database-specific optimizations.
"""

import logging
from sqlalchemy import or_, func, literal

from app.models.message import Message
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def build_search_query(q: str):
    """Build a database-specific search filter for messages.

    Args:
        q: The search query string

    Returns:
        A SQLAlchemy filter condition that searches both original_text and translated_text

    Notes:
        - SQLite: Uses LIKE with case-insensitive matching
        - PostgreSQL: Uses trigram similarity (%) for better performance
    """
    if settings.use_sqlite:
        # SQLite: Use LIKE with case-insensitive matching
        search_term = f"%{q}%"
        search_filter = or_(
            Message.original_text.ilike(search_term),
            Message.translated_text.ilike(search_term),
        )
    else:
        # PostgreSQL: Use trigram similarity for better performance
        search_filter = or_(
            Message.original_text.op("%")(q),
            Message.translated_text.op("%")(q),
        )

    return search_filter
