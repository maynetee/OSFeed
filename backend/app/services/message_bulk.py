from __future__ import annotations

from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.message import Message
from app.services.publisher import publish_message_event

settings = get_settings()


async def bulk_insert_messages(db: AsyncSession, rows: list[dict[str, Any]]) -> int:
    """Insert messages in bulk with conflict-safe semantics."""
    if not rows:
        return 0

    if settings.use_sqlite:
        stmt = sqlite_insert(Message).values(rows)
    else:
        stmt = pg_insert(Message).values(rows)

    stmt = stmt.on_conflict_do_nothing(
        index_elements=["channel_id", "telegram_message_id"],
    )
    result = await db.execute(stmt)
    count = result.rowcount or 0
    
    if count > 0:
        # We don't get the exact inserted IDs from on_conflict_do_nothing easily in generic SQL.
        # But we know the rows we attempted.
        # For simplicity, we signal "new messages" for these channels.
        # Group by channel
        message_ids = [str(r.get("id")) for r in rows if r.get("id")]
        # Ideally we'd group by channel_id and fire per channel, but firing once is okay for now.
        # The frontend/subscriber will fetch latest.
        await publish_message_event("message:new", message_ids)

    return count
