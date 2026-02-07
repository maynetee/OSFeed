"""add username/country to users and contact_sales_leads table

Revision ID: g9b3c4d5e6f7
Revises: f8a2b3c4d5e6
Create Date: 2026-02-07 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g9b3c4d5e6f7'
down_revision: Union[str, None] = 'f8a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add username and country to users table
    op.add_column('users', sa.Column('username', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('country', sa.String(2), nullable=True))
    op.create_unique_constraint('uq_users_username', 'users', ['username'])

    # Create contact_sales_leads table
    op.create_table(
        'contact_sales_leads',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('company', sa.String(100), nullable=False),
        sa.Column('job_title', sa.String(100), nullable=False),
        sa.Column('company_size', sa.String(20), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('contact_sales_leads')
    op.drop_constraint('uq_users_username', 'users', type_='unique')
    op.drop_column('users', 'country')
    op.drop_column('users', 'username')
