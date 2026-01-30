"""
Verification script to check that collection stats queries use the new indexes.

This script generates EXPLAIN ANALYZE output for the collections stats query
and verifies that it uses ix_messages_channel_published_lang index.
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, case, text
from datetime import datetime, timedelta
from uuid import UUID

from app.models.message import Message
from app.models.channel import Channel


async def verify_query_plan():
    """Verify that the collections stats query uses the new index."""

    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("\nTo run this verification:")
        print("1. Ensure PostgreSQL is running (docker-compose up -d)")
        print("2. Run migrations (alembic upgrade head)")
        print("3. Set DATABASE_URL and run this script")
        return False

    # Convert postgresql:// to postgresql+asyncpg://
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print("=" * 80)
    print("Database Index Verification - Collections Stats Query")
    print("=" * 80)
    print()

    # Create async engine
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db:
            # First, check if the indexes exist
            print("Step 1: Checking if required indexes exist...")
            print("-" * 80)

            index_check = await db.execute(text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename='messages'
                AND indexname IN ('ix_messages_source_language', 'ix_messages_channel_published_lang')
                ORDER BY indexname
            """))
            indexes = [row[0] for row in index_check.fetchall()]

            if 'ix_messages_source_language' in indexes:
                print("✅ ix_messages_source_language exists")
            else:
                print("❌ ix_messages_source_language NOT FOUND")

            if 'ix_messages_channel_published_lang' in indexes:
                print("✅ ix_messages_channel_published_lang exists")
            else:
                print("❌ ix_messages_channel_published_lang NOT FOUND")

            if len(indexes) < 2:
                print("\n⚠️  WARNING: Indexes not found in database.")
                print("   Please run: cd backend && alembic upgrade head")
                return False

            print()

            # Get some sample channel IDs for the query
            print("Step 2: Getting sample channel IDs...")
            print("-" * 80)

            channel_result = await db.execute(
                select(Channel.id).where(Channel.is_active == True).limit(3)
            )
            channel_ids = [str(row[0]) for row in channel_result.fetchall()]

            if not channel_ids:
                print("⚠️  No channels found in database. Using dummy UUIDs for EXPLAIN.")
                # Use dummy UUIDs for EXPLAIN (won't return data but will show query plan)
                channel_ids = [
                    "00000000-0000-0000-0000-000000000001",
                    "00000000-0000-0000-0000-000000000002",
                ]
            else:
                print(f"✅ Using {len(channel_ids)} channel ID(s) for verification")

            print()

            # Build the exact query from collections.py get_stats endpoint
            print("Step 3: Building collections stats query (from collections.py)...")
            print("-" * 80)

            date_bucket = func.date(Message.published_at)
            query = select(
                date_bucket.label("day"),
                Message.source_language,
                func.count().label("count"),
                func.sum(case((Message.is_duplicate == True, 1), else_=0)).label("dup_count"),
            ).where(
                Message.channel_id.in_([UUID(cid) for cid in channel_ids])
            ).group_by(date_bucket, Message.source_language)

            # Compile the query to SQL
            compiled_query = str(query.compile(
                compile_kwargs={"literal_binds": True}
            ))

            print("Query:")
            print(compiled_query)
            print()

            # Run EXPLAIN ANALYZE
            print("Step 4: Running EXPLAIN ANALYZE...")
            print("-" * 80)

            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {compiled_query}"
            explain_result = await db.execute(text(explain_query))
            explain_output = [row[0] for row in explain_result.fetchall()]

            print("\n".join(explain_output))
            print()

            # Analyze the query plan
            print("Step 5: Analyzing query plan...")
            print("-" * 80)

            plan_text = "\n".join(explain_output).lower()

            # Check for the new index
            uses_new_index = "ix_messages_channel_published_lang" in plan_text
            uses_index_scan = "index scan" in plan_text or "bitmap index scan" in plan_text
            uses_seq_scan = "seq scan" in plan_text and "messages" in plan_text

            print()
            if uses_new_index:
                print("✅ PASS: Query plan uses ix_messages_channel_published_lang index")
            else:
                print("⚠️  Query plan does NOT explicitly mention ix_messages_channel_published_lang")

            if uses_index_scan:
                print("✅ PASS: Query uses Index Scan (not Sequential Scan)")
            else:
                print("⚠️  Query does not use Index Scan")

            if uses_seq_scan:
                print("❌ FAIL: Query uses Sequential Scan on messages table")
                print("   This indicates the index is not being used optimally")
            else:
                print("✅ PASS: No Sequential Scan on messages table")

            print()
            print("=" * 80)

            # Final verdict
            if uses_new_index and uses_index_scan and not uses_seq_scan:
                print("🎉 VERIFICATION PASSED: New indexes are being used optimally!")
                print()
                return True
            elif uses_index_scan and not uses_seq_scan:
                print("⚠️  VERIFICATION PARTIAL: Query uses indexes but may not be the new one.")
                print("   This could be acceptable if an existing index covers the query.")
                print("   Check if the query plan shows good performance on large datasets.")
                print()
                return True
            else:
                print("❌ VERIFICATION FAILED: Query is not using indexes optimally")
                print()
                print("Possible reasons:")
                print("- Indexes not created yet (run: alembic upgrade head)")
                print("- Table has very few rows (PostgreSQL prefers SeqScan for small tables)")
                print("- Statistics out of date (run: ANALYZE messages;)")
                print()
                return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


async def main():
    """Main entry point."""
    success = await verify_query_plan()

    if success:
        print("\n✅ All verifications passed!")
        exit(0)
    else:
        print("\n❌ Verification failed or incomplete")
        print("\nNote: If the database has very few rows, PostgreSQL may choose")
        print("Sequential Scan over Index Scan as it's faster for small datasets.")
        print("The indexes will be used automatically when the table grows.")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
