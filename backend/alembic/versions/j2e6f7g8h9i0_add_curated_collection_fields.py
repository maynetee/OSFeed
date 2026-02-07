"""add curated collection fields

Revision ID: j2e6f7g8h9i0
Revises: h0c4d5e6f7g8
Create Date: 2026-02-07 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'j2e6f7g8h9i0'
down_revision: Union[str, None] = 'h0c4d5e6f7g8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make user_id nullable (curated collections have no owner)
    with op.batch_alter_table('collections') as batch_op:
        batch_op.alter_column('user_id', existing_type=sa.String(length=36), nullable=True)

    op.add_column('collections', sa.Column('is_curated', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('collections', sa.Column('curator', sa.String(length=100), nullable=True))
    op.add_column('collections', sa.Column('region', sa.String(length=50), nullable=True))
    op.add_column('collections', sa.Column('topic', sa.String(length=50), nullable=True))
    op.add_column('collections', sa.Column('thumbnail_url', sa.String(length=500), nullable=True))
    op.add_column('collections', sa.Column('last_curated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('collections', sa.Column('curated_channel_usernames', sa.JSON(), nullable=True))
    op.create_index('ix_collections_is_curated', 'collections', ['is_curated'])


def downgrade() -> None:
    op.drop_index('ix_collections_is_curated', table_name='collections')
    op.drop_column('collections', 'curated_channel_usernames')
    op.drop_column('collections', 'last_curated_at')
    op.drop_column('collections', 'thumbnail_url')
    op.drop_column('collections', 'topic')
    op.drop_column('collections', 'region')
    op.drop_column('collections', 'curator')
    op.drop_column('collections', 'is_curated')

    with op.batch_alter_table('collections') as batch_op:
        batch_op.alter_column('user_id', existing_type=sa.String(length=36), nullable=False)
