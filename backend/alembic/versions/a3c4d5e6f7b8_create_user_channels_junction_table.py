"""Create user_channels junction table for many-to-many relationship

Revision ID: a3c4d5e6f7b8
Revises: f2b3c4d5e6a7
Create Date: 2026-01-18 20:00:00.000000

Optimizations from OPTIMIZATION_PLAN.md Phase 5:
- Junction table for shared channel data across users
- Prevents redundant Telegram API calls when multiple users add same channel
- Includes indexes for efficient lookups on both user_id and channel_id
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a3c4d5e6f7b8"
down_revision: Union[str, None] = "f2b3c4d5e6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create junction table for many-to-many user-channel relationship
    # Enables shared channel data: when user B adds a channel user A already added,
    # the system can link to existing channel instead of re-fetching from Telegram
    op.create_table(
        "user_channels",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("channel_id", sa.UUID(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Unique constraint: a user can only be linked to a channel once
    op.create_unique_constraint(
        "uq_user_channels_user_channel",
        "user_channels",
        ["user_id", "channel_id"],
    )

    # Index for finding all channels for a specific user
    # Query pattern: SELECT * FROM user_channels WHERE user_id = ?
    op.create_index(
        "ix_user_channels_user_id",
        "user_channels",
        ["user_id"],
        unique=False,
    )

    # Index for finding all users subscribed to a specific channel
    # Query pattern: SELECT * FROM user_channels WHERE channel_id = ?
    op.create_index(
        "ix_user_channels_channel_id",
        "user_channels",
        ["channel_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_channels_channel_id", table_name="user_channels")
    op.drop_index("ix_user_channels_user_id", table_name="user_channels")
    op.drop_constraint("uq_user_channels_user_channel", "user_channels", type_="unique")
    op.drop_table("user_channels")
