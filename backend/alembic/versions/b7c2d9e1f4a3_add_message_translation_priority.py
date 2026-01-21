"""Add translation priority to messages

Revision ID: b7c2d9e1f4a3
Revises: 3a400dd0fc64
Create Date: 2026-01-21 12:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7c2d9e1f4a3"
down_revision: Union[str, None] = "3a400dd0fc64"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("translation_priority", sa.String(length=10), nullable=False, server_default="normal"),
    )


def downgrade() -> None:
    op.drop_column("messages", "translation_priority")
