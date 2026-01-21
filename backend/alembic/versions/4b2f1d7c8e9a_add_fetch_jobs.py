"""add fetch jobs

Revision ID: 4b2f1d7c8e9a
Revises: 3a400dd0fc64
Create Date: 2026-01-17 09:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4b2f1d7c8e9a'
down_revision: Union[str, None] = '3a400dd0fc64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'fetch_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('days', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('stage', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('total_messages', sa.Integer(), nullable=True),
        sa.Column('new_messages', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_fetch_jobs_channel_created', 'fetch_jobs', ['channel_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_fetch_jobs_channel_id'), 'fetch_jobs', ['channel_id'], unique=False)
    op.create_index(op.f('ix_fetch_jobs_status'), 'fetch_jobs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_fetch_jobs_status'), table_name='fetch_jobs')
    op.drop_index(op.f('ix_fetch_jobs_channel_id'), table_name='fetch_jobs')
    op.drop_index('ix_fetch_jobs_channel_created', table_name='fetch_jobs')
    op.drop_table('fetch_jobs')
