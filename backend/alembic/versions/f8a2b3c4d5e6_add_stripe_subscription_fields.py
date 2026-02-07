"""add stripe subscription fields to users

Revision ID: f8a2b3c4d5e6
Revises: c4d5e6f7a8b9
Create Date: 2026-02-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8a2b3c4d5e6'
down_revision: Union[str, None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [c['name'] for c in inspector.get_columns('users')]

    if 'stripe_customer_id' not in existing_columns:
        op.add_column('users', sa.Column('stripe_customer_id', sa.String(255), nullable=True))
    if 'stripe_subscription_id' not in existing_columns:
        op.add_column('users', sa.Column('stripe_subscription_id', sa.String(255), nullable=True))
    if 'subscription_plan' not in existing_columns:
        op.add_column('users', sa.Column('subscription_plan', sa.String(20), server_default='none', nullable=True))
    if 'subscription_status' not in existing_columns:
        op.add_column('users', sa.Column('subscription_status', sa.String(20), server_default='none', nullable=True))
    if 'subscription_period_end' not in existing_columns:
        op.add_column('users', sa.Column('subscription_period_end', sa.DateTime(timezone=True), nullable=True))

    existing_constraints = [c['name'] for c in inspector.get_unique_constraints('users')]
    if 'uq_users_stripe_customer_id' not in existing_constraints:
        op.create_unique_constraint('uq_users_stripe_customer_id', 'users', ['stripe_customer_id'])


def downgrade() -> None:
    op.drop_constraint('uq_users_stripe_customer_id', 'users', type_='unique')
    op.drop_column('users', 'subscription_period_end')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'subscription_plan')
    op.drop_column('users', 'stripe_subscription_id')
    op.drop_column('users', 'stripe_customer_id')
