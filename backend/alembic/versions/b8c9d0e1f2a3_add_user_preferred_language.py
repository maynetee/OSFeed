"""Add preferred_language column to users table

Revision ID: b8c9d0e1f2a3
Revises: a1b2c3d4e5f6
Create Date: 2026-01-29 08:00:00.000000

Feature: Conditional Channel Translation Based on User Languages
- Stores user's preferred language for translation decision logic
- When all users of a channel share the same language as the channel content,
  messages won't be translated (saving API costs)
- Default 'en' matches settings.preferred_language
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add preferred_language column to users table
    # Used to determine if channel messages need translation based on subscriber languages
    op.add_column(
        "users",
        sa.Column("preferred_language", sa.String(10), server_default="en", nullable=False),
    )

    # Index for efficient lookups when checking channel translation requirements
    # Query pattern: SELECT preferred_language FROM users WHERE id IN (SELECT user_id FROM user_channels WHERE channel_id = ?)
    op.create_index(
        "ix_users_preferred_language",
        "users",
        ["preferred_language"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_users_preferred_language", table_name="users")
    op.drop_column("users", "preferred_language")
