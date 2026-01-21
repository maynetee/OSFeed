"""add messages cursor index

Revision ID: c2f4a9d1e7b3
Revises: 8b7f2c1d3e4a
Create Date: 2026-01-21 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c2f4a9d1e7b3"
down_revision: Union[str, None] = "8b7f2c1d3e4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_messages_channel_published_id",
        "messages",
        ["channel_id", "published_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_messages_channel_published_id", table_name="messages")
