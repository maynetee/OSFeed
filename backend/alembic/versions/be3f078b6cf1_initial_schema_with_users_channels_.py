"""Initial schema with users, channels, messages, summaries

Revision ID: be3f078b6cf1
Revises: 
Create Date: 2026-01-16 11:44:31.539651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'be3f078b6cf1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type only if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                CREATE TYPE userrole AS ENUM ('admin', 'analyst', 'viewer');
            END IF;
        END$$;
    """)

    # Use postgresql.ENUM with create_type=False since we handle enum creation manually above
    user_role_enum = postgresql.ENUM("admin", "analyst", "viewer", name="userrole", create_type=False)

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("consent_given_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_retention_days", sa.Integer(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "channels",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("detected_language", sa.String(length=10), nullable=True),
        sa.Column("subscriber_count", sa.BigInteger(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("fetch_config", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index(op.f("ix_channels_telegram_id"), "channels", ["telegram_id"], unique=False)
    op.create_index(op.f("ix_channels_username"), "channels", ["username"], unique=False)
    op.create_index(op.f("ix_channels_is_active"), "channels", ["is_active"], unique=False)
    op.create_index("ix_channels_active_username", "channels", ["is_active", "username"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("channel_id", sa.UUID(), nullable=False),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=True),
        sa.Column("translated_text", sa.Text(), nullable=True),
        sa.Column("source_language", sa.String(length=10), nullable=True),
        sa.Column("target_language", sa.String(length=10), nullable=True),
        sa.Column("media_type", sa.String(length=50), nullable=True),
        sa.Column("media_urls", sa.JSON(), nullable=True),
        sa.Column("is_duplicate", sa.Boolean(), nullable=True),
        sa.Column("originality_score", sa.SmallInteger(), nullable=True),
        sa.Column("duplicate_group_id", sa.UUID(), nullable=True),
        sa.Column("embedding_id", sa.String(length=255), nullable=True),
        sa.Column("entities", sa.JSON(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("translated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_messages_channel_id"), "messages", ["channel_id"], unique=False)
    op.create_index(op.f("ix_messages_published_at"), "messages", ["published_at"], unique=False)
    op.create_index(op.f("ix_messages_is_duplicate"), "messages", ["is_duplicate"], unique=False)
    op.create_index("ix_messages_channel_published", "messages", ["channel_id", "published_at"], unique=False)
    op.create_index("ix_messages_channel_telegram_id", "messages", ["channel_id", "telegram_message_id"], unique=True)
    op.create_index(
        "ix_messages_duplicate_group",
        "messages",
        ["duplicate_group_id"],
        unique=False,
        postgresql_where=sa.text("duplicate_group_id IS NOT NULL"),
    )

    op.create_table(
        "summaries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("digest_type", sa.String(length=50), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("content_html", sa.Text(), nullable=True),
        sa.Column("message_count", sa.Integer(), nullable=True),
        sa.Column("channels_covered", sa.Integer(), nullable=True),
        sa.Column("duplicates_filtered", sa.Integer(), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_summaries_user_id"), "summaries", ["user_id"], unique=False)
    op.create_index(op.f("ix_summaries_digest_type"), "summaries", ["digest_type"], unique=False)
    op.create_index(
        "ix_summaries_user_type_date",
        "summaries",
        ["user_id", "digest_type", "generated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_summaries_user_type_date", table_name="summaries")
    op.drop_index(op.f("ix_summaries_digest_type"), table_name="summaries")
    op.drop_index(op.f("ix_summaries_user_id"), table_name="summaries")
    op.drop_table("summaries")

    op.drop_index("ix_messages_duplicate_group", table_name="messages", postgresql_where=sa.text("duplicate_group_id IS NOT NULL"))
    op.drop_index("ix_messages_channel_telegram_id", table_name="messages")
    op.drop_index("ix_messages_channel_published", table_name="messages")
    op.drop_index(op.f("ix_messages_is_duplicate"), table_name="messages")
    op.drop_index(op.f("ix_messages_published_at"), table_name="messages")
    op.drop_index(op.f("ix_messages_channel_id"), table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_channels_active_username", table_name="channels")
    op.drop_index(op.f("ix_channels_is_active"), table_name="channels")
    op.drop_index(op.f("ix_channels_username"), table_name="channels")
    op.drop_index(op.f("ix_channels_telegram_id"), table_name="channels")
    op.drop_table("channels")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
