"""add summaries table

Revision ID: n6i0j1k2l3m4
Revises: m5h9i0j1k2l3
Create Date: 2026-02-07 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'n6i0j1k2l3m4'
down_revision: Union[str, None] = 'm5h9i0j1k2l3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'summaries' not in existing_tables:
        op.create_table(
            'summaries',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'),
                       nullable=False, index=True),
            sa.Column('collection_id', postgresql.UUID(as_uuid=True),
                       sa.ForeignKey('collections.id', ondelete='SET NULL'), nullable=True),
            sa.Column('channel_ids', sa.JSON(), server_default='[]'),
            sa.Column('date_range_start', sa.DateTime(timezone=True), nullable=False),
            sa.Column('date_range_end', sa.DateTime(timezone=True), nullable=False),
            sa.Column('summary_text', sa.Text(), nullable=False),
            sa.Column('key_themes', sa.JSON(), server_default='[]'),
            sa.Column('notable_events', sa.JSON(), server_default='[]'),
            sa.Column('message_count', sa.Integer(), server_default='0'),
            sa.Column('model_used', sa.String(50), nullable=True),
            sa.Column('generation_time_seconds', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        )


def downgrade() -> None:
    op.drop_table('summaries')
