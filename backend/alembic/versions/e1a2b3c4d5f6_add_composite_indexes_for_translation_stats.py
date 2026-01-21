"""Add composite indexes for translation and stats queries

Revision ID: e1a2b3c4d5f6
Revises: d3b7c1a8e2f4
Create Date: 2026-01-18 19:58:00.000000

Optimizations from OPTIMIZATION_PLAN.md Phase 2:
- Composite index for translation queries: (channel_id, needs_translation, translation_priority)
- Composite index for stats queries: (published_at, is_duplicate)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e1a2b3c4d5f6"
down_revision: Union[str, None] = "d3b7c1a8e2f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite index for translation query optimization
    # Used by: translate_pending_messages_job, /api/messages/translate
    # Query pattern: WHERE channel_id = ? AND needs_translation = TRUE ORDER BY translation_priority
    op.create_index(
        "ix_messages_translation_query",
        "messages",
        ["channel_id", "needs_translation", "translation_priority"],
        unique=False,
    )

    # Composite index for stats query optimization
    # Used by: /api/stats endpoints for date-range queries filtering duplicates
    # Query pattern: WHERE published_at BETWEEN ? AND ? AND is_duplicate = FALSE
    op.create_index(
        "ix_messages_stats_query",
        "messages",
        ["published_at", "is_duplicate"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_messages_stats_query", table_name="messages")
    op.drop_index("ix_messages_translation_query", table_name="messages")
