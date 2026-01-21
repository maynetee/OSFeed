"""make channel telegram_id nullable

Revision ID: 6f1b3c9d2a1e
Revises: 4b2f1d7c8e9a
Create Date: 2026-01-17 09:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f1b3c9d2a1e'
down_revision: Union[str, None] = '4b2f1d7c8e9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('channels', 'telegram_id', existing_type=sa.BigInteger(), nullable=True)


def downgrade() -> None:
    op.alter_column('channels', 'telegram_id', existing_type=sa.BigInteger(), nullable=False)
