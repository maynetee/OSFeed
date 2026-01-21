"""add needs_translation flag to messages

Revision ID: d3b7c1a8e2f4
Revises: c2f4a9d1e7b3
Create Date: 2026-01-21 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d3b7c1a8e2f4"
down_revision: Union[str, None] = "c2f4a9d1e7b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("needs_translation", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.create_index(
        op.f("ix_messages_needs_translation"),
        "messages",
        ["needs_translation"],
        unique=False,
    )
    op.execute("UPDATE messages SET needs_translation = FALSE WHERE translated_text IS NOT NULL")


def downgrade() -> None:
    op.drop_index(op.f("ix_messages_needs_translation"), table_name="messages")
    op.drop_column("messages", "needs_translation")
