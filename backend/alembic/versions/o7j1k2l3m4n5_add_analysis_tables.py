"""add analysis tables for intelligence features

Revision ID: o7j1k2l3m4n5
Revises: n6i0j1k2l3m4
Create Date: 2026-02-07 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'o7j1k2l3m4n5'
down_revision: Union[str, None] = 'n6i0j1k2l3m4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Escalation scores
    op.create_table(
        'escalation_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('level', sa.String(10), nullable=False),
        sa.Column('factors', sa.JSON(), default=[]),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_escalation_scores_message_id', 'escalation_scores', ['message_id'])
    op.create_index('ix_escalation_scores_level', 'escalation_scores', ['level'])
    op.create_index('ix_escalation_scores_score', 'escalation_scores', ['score'])

    # Correlations
    op.create_table(
        'correlations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('duplicate_group_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('analysis_text', sa.Text(), nullable=True),
        sa.Column('consistent_facts', sa.JSON(), default=[]),
        sa.Column('unique_details', sa.JSON(), default=[]),
        sa.Column('contradictions', sa.JSON(), default=[]),
        sa.Column('source_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_correlations_duplicate_group_id', 'correlations', ['duplicate_group_id'])

    # Detected patterns
    op.create_table(
        'detected_patterns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pattern_type', sa.String(30), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('evidence_message_ids', sa.JSON(), default=[]),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_detected_patterns_type', 'detected_patterns', ['pattern_type'])
    op.create_index('ix_detected_patterns_detected_at', 'detected_patterns', ['detected_at'])

    # Timelines
    op.create_table(
        'timelines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('topic', sa.String(200), nullable=True),
        sa.Column('collection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('collections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('events', sa.JSON(), default=[]),
        sa.Column('date_range_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('date_range_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('message_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_timelines_user_id', 'timelines', ['user_id'])


def downgrade() -> None:
    op.drop_table('timelines')
    op.drop_table('detected_patterns')
    op.drop_table('correlations')
    op.drop_table('escalation_scores')
