"""add fetch job processed messages

Revision ID: 8b7f2c1d3e4a
Revises: 6f1b3c9d2a1e
Create Date: 2026-01-17 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b7f2c1d3e4a'
down_revision: Union[str, None] = '6f1b3c9d2a1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('fetch_jobs', sa.Column('processed_messages', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('fetch_jobs', 'processed_messages')
