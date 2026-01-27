"""Add performance indexes (composite channel+published+dedup)

Revision ID: a1b2c3d4e5f6
Revises: 2e6f3c8958da
Create Date: 2026-01-27 12:00:00.000000

Performance optimization:
- Composite index for filtered timeline queries: (channel_id, published_at, is_duplicate)
  Used by collection compare, list, and overview endpoints that filter by channel
  and date range while excluding duplicates.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "2e6f3c8958da"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite index for filtered timeline queries (channel + date + dedup)
    # Used by: /api/collections compare, list, overview endpoints
    # Query pattern: WHERE channel_id = ? AND published_at BETWEEN ? AND ? AND is_duplicate = FALSE
    op.create_index(
        "ix_messages_channel_published_dedup",
        "messages",
        ["channel_id", "published_at", "is_duplicate"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_messages_channel_published_dedup", table_name="messages")
