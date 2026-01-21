"""Create message_translations table for multi-language translation cache

Revision ID: b4d5e6f7a8c9
Revises: a3c4d5e6f7b8
Create Date: 2026-01-18 20:01:00.000000

Optimizations from OPTIMIZATION_PLAN.md Phase 5:
- Storage for translations of messages to multiple target languages
- Cache-first approach: check DB before calling GPT API
- Estimated savings: 99x fewer GPT API calls for popular messages
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b4d5e6f7a8c9"
down_revision: Union[str, None] = "a3c4d5e6f7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create table for caching translations in multiple languages
    # When user requests translation, check this table first before calling GPT
    # 100 users requesting same message in French = 1 GPT call + 99 DB lookups
    op.create_table(
        "message_translations",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("message_id", sa.UUID(), nullable=False),
        sa.Column("target_lang", sa.String(length=10), nullable=False),  # e.g., "en", "fr", "de", "es"
        sa.Column("translated_text", sa.Text(), nullable=False),
        sa.Column("translated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("translated_by", sa.UUID(), nullable=True),  # User who triggered the translation
        sa.Column("token_count", sa.Integer(), nullable=True),  # Track token usage for analytics
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["translated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Unique constraint: one translation per message per target language
    # Prevents duplicate translations and enables efficient upserts
    op.create_unique_constraint(
        "uq_message_translations_message_lang",
        "message_translations",
        ["message_id", "target_lang"],
    )

    # Composite index for fast lookup of cached translations
    # Query pattern: SELECT * FROM message_translations WHERE message_id = ? AND target_lang = ?
    op.create_index(
        "ix_message_translations_lookup",
        "message_translations",
        ["message_id", "target_lang"],
        unique=False,
    )

    # Index for finding all translations for a message (when displaying all available translations)
    # Query pattern: SELECT * FROM message_translations WHERE message_id = ?
    op.create_index(
        "ix_message_translations_message_id",
        "message_translations",
        ["message_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_message_translations_message_id", table_name="message_translations")
    op.drop_index("ix_message_translations_lookup", table_name="message_translations")
    op.drop_constraint("uq_message_translations_message_lang", "message_translations", type_="unique")
    op.drop_table("message_translations")
