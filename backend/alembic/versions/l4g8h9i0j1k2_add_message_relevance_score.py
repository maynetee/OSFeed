"""add message relevance_score column

Revision ID: l4g8h9i0j1k2
Revises: k3f7g8h9i0j1
Create Date: 2026-02-07 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'l4g8h9i0j1k2'
down_revision: Union[str, None] = 'k3f7g8h9i0j1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('messages', sa.Column('relevance_score', sa.Float(), nullable=True))
    op.create_index('ix_messages_relevance_score', 'messages', ['relevance_score'])


def downgrade() -> None:
    op.drop_index('ix_messages_relevance_score', table_name='messages')
    op.drop_column('messages', 'relevance_score')
