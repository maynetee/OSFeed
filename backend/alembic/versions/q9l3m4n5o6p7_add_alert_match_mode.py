"""add alert match_mode and last_evaluated_at

Revision ID: q9l3m4n5o6p7
Revises: p8k2l3m4n5o6
Create Date: 2026-02-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'q9l3m4n5o6p7'
down_revision: Union[str, None] = 'p8k2l3m4n5o6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('alerts', sa.Column('match_mode', sa.String(10), server_default='any', nullable=False))
    op.add_column('alerts', sa.Column('last_evaluated_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('alerts', 'last_evaluated_at')
    op.drop_column('alerts', 'match_mode')
