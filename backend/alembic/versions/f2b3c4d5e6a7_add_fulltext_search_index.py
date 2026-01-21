"""Add full-text search index for messages

Revision ID: f2b3c4d5e6a7
Revises: e1a2b3c4d5f6
Create Date: 2026-01-18 19:59:00.000000

Optimizations from OPTIMIZATION_PLAN.md Phase 2:
- GIN index with pg_trgm for ILIKE pattern matching on original_text and translated_text
- Enables efficient full-text search without LIKE '%pattern%' full table scans
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f2b3c4d5e6a7"
down_revision: Union[str, None] = "e1a2b3c4d5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension for trigram-based similarity search
    # Required for GIN indexes supporting ILIKE and similarity queries
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # GIN index on original_text for ILIKE pattern matching
    # Used by: /api/messages search functionality
    # Query pattern: WHERE original_text ILIKE '%search_term%'
    op.execute(
        """
        CREATE INDEX ix_messages_original_text_trgm
        ON messages
        USING GIN (original_text gin_trgm_ops)
        """
    )

    # GIN index on translated_text for ILIKE pattern matching
    # Used by: /api/messages search on translated content
    # Query pattern: WHERE translated_text ILIKE '%search_term%'
    op.execute(
        """
        CREATE INDEX ix_messages_translated_text_trgm
        ON messages
        USING GIN (translated_text gin_trgm_ops)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_messages_translated_text_trgm")
    op.execute("DROP INDEX IF EXISTS ix_messages_original_text_trgm")
    # Note: We don't drop pg_trgm extension as other parts of the system may use it
