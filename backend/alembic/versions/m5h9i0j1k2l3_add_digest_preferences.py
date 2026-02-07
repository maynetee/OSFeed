"""add digest_preferences table

Revision ID: m5h9i0j1k2l3
Revises: l4g8h9i0j1k2
Create Date: 2026-02-07 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'm5h9i0j1k2l3'
down_revision: Union[str, None] = 'l4g8h9i0j1k2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'digest_preferences' not in existing_tables:
        op.create_table(
            'digest_preferences',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('enabled', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('frequency', sa.String(length=10), nullable=True, server_default='daily'),
            sa.Column('send_hour', sa.Integer(), nullable=True, server_default='8'),
            sa.Column('collection_ids', sa.JSON(), nullable=True),
            sa.Column('max_messages', sa.Integer(), nullable=True, server_default='20'),
            sa.Column('last_sent_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_digest_preferences_user_id', 'digest_preferences', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_digest_preferences_user_id', table_name='digest_preferences')
    op.drop_table('digest_preferences')
