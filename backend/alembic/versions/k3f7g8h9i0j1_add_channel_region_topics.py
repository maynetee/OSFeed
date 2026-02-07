"""add channel region and topics columns

Revision ID: k3f7g8h9i0j1
Revises: j2e6f7g8h9i0
Create Date: 2026-02-07 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'k3f7g8h9i0j1'
down_revision: Union[str, None] = 'j2e6f7g8h9i0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('channels', sa.Column('region', sa.String(50), nullable=True))
    op.add_column('channels', sa.Column('topics', sa.JSON(), nullable=True))
    op.create_index('ix_channels_region', 'channels', ['region'])


def downgrade() -> None:
    op.drop_index('ix_channels_region', table_name='channels')
    op.drop_column('channels', 'topics')
    op.drop_column('channels', 'region')
