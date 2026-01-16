#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone

import asyncpg


def parse_datetime(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def parse_json(value):
    if value in (None, ""):
        return None
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None


def build_postgres_dsn():
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "telescope_db")
    user = os.getenv("POSTGRES_USER", "telescope_user")
    password = os.getenv("POSTGRES_PASSWORD", "")
    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return f"postgresql://{user}@{host}:{port}/{db}"


def load_sqlite_rows(sqlite_path):
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM channels")
    channels = [dict(row) for row in cur.fetchall()]
    cur.execute("SELECT * FROM messages")
    messages = [dict(row) for row in cur.fetchall()]
    cur.execute("SELECT * FROM summaries")
    summaries = [dict(row) for row in cur.fetchall()]
    conn.close()
    return channels, messages, summaries


async def migrate(sqlite_path, postgres_dsn, dry_run):
    channels, messages, summaries = load_sqlite_rows(sqlite_path)
    channel_id_map = {}
    duplicate_group_map = {}

    channel_rows = []
    for channel in channels:
        new_id = uuid.uuid4()
        channel_id_map[channel["id"]] = new_id
        telegram_id = channel.get("telegram_id")
        try:
            telegram_id = int(telegram_id) if telegram_id is not None else None
        except (TypeError, ValueError):
            telegram_id = None

        channel_rows.append(
            (
                new_id,
                telegram_id,
                channel.get("username"),
                channel.get("title"),
                channel.get("description"),
                channel.get("language"),
                channel.get("subscriber_count"),
                True,
                {"frequency_minutes": 5, "max_messages": 100},
                parse_datetime(channel.get("created_at")),
                None,
                parse_datetime(channel.get("last_fetched_at")),
            )
        )

    message_rows = []
    skipped_messages = 0
    for message in messages:
        channel_uuid = channel_id_map.get(message.get("channel_id"))
        if not channel_uuid:
            skipped_messages += 1
            continue

        duplicate_group_id = message.get("duplicate_group_id")
        if duplicate_group_id:
            if duplicate_group_id not in duplicate_group_map:
                duplicate_group_map[duplicate_group_id] = uuid.uuid4()
            duplicate_group_id = duplicate_group_map[duplicate_group_id]
        else:
            duplicate_group_id = None

        message_rows.append(
            (
                uuid.uuid4(),
                channel_uuid,
                message.get("telegram_message_id"),
                message.get("original_text"),
                message.get("translated_text"),
                message.get("source_language"),
                "fr",
                message.get("media_type"),
                parse_json(message.get("media_urls")) or [],
                bool(message.get("is_duplicate")),
                100,
                duplicate_group_id,
                None,
                {"persons": [], "locations": [], "organizations": []},
                parse_datetime(message.get("published_at")),
                parse_datetime(message.get("fetched_at")),
                None,
            )
        )

    summary_rows = []
    for summary in summaries:
        summary_rows.append(
            (
                uuid.uuid4(),
                None,
                summary.get("summary_type") or "daily",
                None,
                summary.get("content"),
                None,
                summary.get("message_count") or 0,
                0,
                0,
                parse_datetime(summary.get("period_start")),
                parse_datetime(summary.get("period_end")),
                {"collections": [], "languages": [], "keywords": []},
                parse_datetime(summary.get("generated_at")),
            )
        )

    if dry_run:
        print(f"Channels to migrate: {len(channel_rows)}")
        print(f"Messages to migrate: {len(message_rows)} (skipped {skipped_messages})")
        print(f"Summaries to migrate: {len(summary_rows)}")
        return

    conn = await asyncpg.connect(postgres_dsn)
    try:
        async with conn.transaction():
            if channel_rows:
                await conn.executemany(
                    """
                    INSERT INTO channels (
                        id, telegram_id, username, title, description, detected_language,
                        subscriber_count, is_active, fetch_config, created_at, updated_at, last_fetched_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """,
                    channel_rows,
                )
            if message_rows:
                await conn.executemany(
                    """
                    INSERT INTO messages (
                        id, channel_id, telegram_message_id, original_text, translated_text, source_language,
                        target_language, media_type, media_urls, is_duplicate, originality_score, duplicate_group_id,
                        embedding_id, entities, published_at, fetched_at, translated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                    """,
                    message_rows,
                )
            if summary_rows:
                await conn.executemany(
                    """
                    INSERT INTO summaries (
                        id, user_id, digest_type, title, content, content_html, message_count, channels_covered,
                        duplicates_filtered, period_start, period_end, filters, generated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    """,
                    summary_rows,
                )
    finally:
        await conn.close()

    print(f"Migrated channels: {len(channel_rows)}")
    print(f"Migrated messages: {len(message_rows)} (skipped {skipped_messages})")
    print(f"Migrated summaries: {len(summary_rows)}")


def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite data into PostgreSQL.")
    parser.add_argument("--sqlite-path", default="data/telescope.db", help="Path to SQLite DB file.")
    parser.add_argument("--postgres-dsn", default=build_postgres_dsn(), help="PostgreSQL DSN.")
    parser.add_argument("--dry-run", action="store_true", help="Print counts without writing.")
    args = parser.parse_args()

    if not os.path.exists(args.sqlite_path):
        raise SystemExit(f"SQLite DB not found: {args.sqlite_path}")

    asyncio.run(migrate(args.sqlite_path, args.postgres_dsn, args.dry_run))


if __name__ == "__main__":
    main()
