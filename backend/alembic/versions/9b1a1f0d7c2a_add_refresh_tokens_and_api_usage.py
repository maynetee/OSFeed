"""Add refresh tokens and API usage tracking

Revision ID: 9b1a1f0d7c2a
Revises: 0f3c3a5c8f2a
Create Date: 2026-01-17 10:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9b1a1f0d7c2a"
down_revision = "0f3c3a5c8f2a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("refresh_token_hash", sa.String(length=128), nullable=True))
    op.add_column(
        "users",
        sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "api_usages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("purpose", sa.String(length=50), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost_usd", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_api_usages_provider_model_time",
        "api_usages",
        ["provider", "model", "created_at"],
    )
    op.create_index(op.f("ix_api_usages_created_at"), "api_usages", ["created_at"])
    op.create_index(op.f("ix_api_usages_model"), "api_usages", ["model"])
    op.create_index(op.f("ix_api_usages_provider"), "api_usages", ["provider"])
    op.create_index(op.f("ix_api_usages_purpose"), "api_usages", ["purpose"])


def downgrade() -> None:
    op.drop_index(op.f("ix_api_usages_purpose"), table_name="api_usages")
    op.drop_index(op.f("ix_api_usages_provider"), table_name="api_usages")
    op.drop_index(op.f("ix_api_usages_model"), table_name="api_usages")
    op.drop_index(op.f("ix_api_usages_created_at"), table_name="api_usages")
    op.drop_index("ix_api_usages_provider_model_time", table_name="api_usages")
    op.drop_table("api_usages")

    op.drop_column("users", "refresh_token_expires_at")
    op.drop_column("users", "refresh_token_hash")
