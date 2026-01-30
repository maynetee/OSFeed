"""Add source_language indexes for analytics queries

Revision ID: a1c2d3e4f5b6
Revises: f2b3c4d5e6a7
Create Date: 2026-01-30 08:00:00.000000

Optimizations for source_language analytics:
- Single column index on source_language for language distribution queries
- Composite index (channel_id, published_at, source_language) for collection stats analytics
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1c2d3e4f5b6"
down_revision: Union[str, None] = "f2b3c4d5e6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Single column index on source_language
    # Used by: Language distribution analytics queries
    # Query pattern: SELECT source_language, COUNT(*) FROM messages GROUP BY source_language
    op.create_index(
        "ix_messages_source_language",
        "messages",
        ["source_language"],
        unique=False,
    )

    # Composite index for collection stats analytics
    # Used by: Collection stats endpoints grouping by date and language
    # Query pattern: WHERE channel_id IN (...) AND published_at >= ? GROUP BY date, source_language
    op.create_index(
        "ix_messages_channel_published_lang",
        "messages",
        ["channel_id", "published_at", "source_language"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_messages_channel_published_lang", table_name="messages")
    op.drop_index("ix_messages_source_language", table_name="messages")
