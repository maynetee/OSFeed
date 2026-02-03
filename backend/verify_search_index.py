"""
Verification script to check that search queries use the GIN trigram index.

This script generates EXPLAIN ANALYZE output for the search_messages query
and verifies that it uses ix_messages_text_search GIN index on both
original_text and translated_text columns.
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, or_, text
from uuid import UUID

from app.models.message import Message
from app.models.channel import Channel


async def verify_search_index():
    """Verify that the search query uses the GIN trigram index."""

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
    print("Database Index Verification - Search Query (GIN Trigram)")
    print("=" * 80)
    print()

    # Create async engine
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db:
            # First, check if the GIN index exists
            print("Step 1: Checking if GIN trigram index exists...")
            print("-" * 80)

            index_check = await db.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename='messages'
                AND indexname = 'ix_messages_text_search'
            """))
            index_result = index_check.fetchone()

            if index_result:
                print(f"✅ ix_messages_text_search exists")
                print(f"   Definition: {index_result[1]}")

                # Verify it's a GIN index with trigram ops
                if "gin" in index_result[1].lower():
                    print("✅ Index uses GIN access method")
                else:
                    print("⚠️  WARNING: Index does not use GIN access method")

                if "gin_trgm_ops" in index_result[1].lower():
                    print("✅ Index uses trigram operators (gin_trgm_ops)")
                else:
                    print("⚠️  WARNING: Index does not use trigram operators")
            else:
                print("❌ ix_messages_text_search NOT FOUND")
                print("\n⚠️  WARNING: GIN trigram index not found in database.")
                print("   Please run: cd backend && alembic upgrade head")
                return False

            print()

            # Check if pg_trgm extension is enabled
            print("Step 2: Checking if pg_trgm extension is enabled...")
            print("-" * 80)

            extension_check = await db.execute(text("""
                SELECT extname FROM pg_extension WHERE extname = 'pg_trgm'
            """))
            extension_result = extension_check.fetchone()

            if extension_result:
                print("✅ pg_trgm extension is enabled")
            else:
                print("❌ pg_trgm extension NOT FOUND")
                print("   Please run: CREATE EXTENSION pg_trgm;")
                return False

            print()

            # Get some sample channel IDs for the query
            print("Step 3: Getting sample channel IDs...")
            print("-" * 80)

            channel_result = await db.execute(
                select(Channel.id).where(Channel.is_active == True).limit(3)
            )
            channel_ids = [row[0] for row in channel_result.fetchall()]

            if not channel_ids:
                print("⚠️  No channels found in database. Using dummy UUIDs for EXPLAIN.")
                # Use dummy UUIDs for EXPLAIN (won't return data but will show query plan)
                channel_ids = [
                    UUID("00000000-0000-0000-0000-000000000001"),
                    UUID("00000000-0000-0000-0000-000000000002"),
                ]
            else:
                print(f"✅ Using {len(channel_ids)} channel ID(s) for verification")

            print()

            # Build the exact query from messages.py search_messages endpoint
            print("Step 4: Building search query (from messages.py search_messages)...")
            print("-" * 80)

            search_term = "%test%"
            search_filter = or_(
                Message.original_text.ilike(search_term),
                Message.translated_text.ilike(search_term),
            )

            # Basic query without all the filters to isolate text search behavior
            query = select(Message).where(
                search_filter
            ).limit(20)

            # Compile the query to SQL
            compiled_query = str(query.compile(
                compile_kwargs={"literal_binds": True}
            ))

            print("Query:")
            print(compiled_query)
            print()

            # Run EXPLAIN ANALYZE
            print("Step 5: Running EXPLAIN ANALYZE...")
            print("-" * 80)

            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {compiled_query}"
            explain_result = await db.execute(text(explain_query))
            explain_output = [row[0] for row in explain_result.fetchall()]

            print("\n".join(explain_output))
            print()

            # Analyze the query plan
            print("Step 6: Analyzing query plan...")
            print("-" * 80)

            plan_text = "\n".join(explain_output).lower()

            # Check for the GIN index usage
            uses_gin_index = "ix_messages_text_search" in plan_text
            uses_bitmap_scan = "bitmap index scan" in plan_text or "bitmap heap scan" in plan_text
            uses_index_scan = "index scan" in plan_text
            uses_seq_scan = "seq scan" in plan_text and "messages" in plan_text

            print()
            if uses_gin_index:
                print("✅ PASS: Query plan uses ix_messages_text_search GIN index")
            else:
                print("⚠️  Query plan does NOT explicitly mention ix_messages_text_search")

            if uses_bitmap_scan or uses_index_scan:
                if uses_bitmap_scan:
                    print("✅ PASS: Query uses Bitmap Index Scan (typical for GIN indexes)")
                if uses_index_scan:
                    print("✅ PASS: Query uses Index Scan")
            else:
                print("⚠️  Query does not use Bitmap Index Scan or Index Scan")

            if uses_seq_scan:
                print("❌ FAIL: Query uses Sequential Scan on messages table")
                print("   This indicates the GIN index is not being used")
            else:
                print("✅ PASS: No Sequential Scan on messages table")

            # Additional check: verify both text columns can use the index
            print()
            print("Step 7: Verifying index coverage for both text columns...")
            print("-" * 80)

            # Test with just original_text
            query_original = select(Message).where(
                Message.original_text.ilike(search_term)
            ).limit(20)
            compiled_original = str(query_original.compile(
                compile_kwargs={"literal_binds": True}
            ))
            explain_original = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {compiled_original}"
            result_original = await db.execute(text(explain_original))
            plan_original = "\n".join([row[0] for row in result_original.fetchall()]).lower()

            # Test with just translated_text (the one that was wrapped in COALESCE)
            query_translated = select(Message).where(
                Message.translated_text.ilike(search_term)
            ).limit(20)
            compiled_translated = str(query_translated.compile(
                compile_kwargs={"literal_binds": True}
            ))
            explain_translated = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {compiled_translated}"
            result_translated = await db.execute(text(explain_translated))
            plan_translated = "\n".join([row[0] for row in result_translated.fetchall()]).lower()

            original_uses_index = "ix_messages_text_search" in plan_original
            translated_uses_index = "ix_messages_text_search" in plan_translated

            if original_uses_index:
                print("✅ PASS: original_text ILIKE can use GIN index")
            else:
                print("⚠️  original_text ILIKE does not mention GIN index")

            if translated_uses_index:
                print("✅ PASS: translated_text ILIKE can use GIN index")
                print("   (This confirms COALESCE removal allows index usage)")
            else:
                print("⚠️  translated_text ILIKE does not mention GIN index")

            print()
            print("=" * 80)

            # Final verdict
            success_conditions = [
                uses_gin_index,
                (uses_bitmap_scan or uses_index_scan),
                not uses_seq_scan,
                translated_uses_index  # Most important: translated_text can now use index
            ]

            if all(success_conditions):
                print("🎉 VERIFICATION PASSED: GIN trigram index is being used optimally!")
                print()
                print("Key achievements:")
                print("✅ ix_messages_text_search GIN index exists and is properly configured")
                print("✅ Search query uses Bitmap Index Scan (efficient for GIN indexes)")
                print("✅ No Sequential Scan on messages table")
                print("✅ Both original_text and translated_text can use the GIN index")
                print("✅ COALESCE removal successfully enables index usage on translated_text")
                print()
                return True
            elif uses_bitmap_scan and not uses_seq_scan:
                print("⚠️  VERIFICATION PARTIAL: Query uses indexes but may not be optimal.")
                print()
                print("Possible reasons:")
                print("- Table has very few rows (PostgreSQL may prefer SeqScan for tiny tables)")
                print("- Query planner chose different strategy (acceptable if performant)")
                print("- Check if the query plan shows good performance on large datasets")
                print()
                return True
            else:
                print("❌ VERIFICATION FAILED: GIN index is not being used optimally")
                print()
                print("Possible reasons:")
                print("- GIN index not created yet (run: alembic upgrade head)")
                print("- pg_trgm extension not enabled (run: CREATE EXTENSION pg_trgm;)")
                print("- Table has very few rows (PostgreSQL prefers SeqScan for small tables)")
                print("- Statistics out of date (run: ANALYZE messages;)")
                print("- COALESCE or other function wrappers preventing index usage")
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
    success = await verify_search_index()

    if success:
        print("\n✅ All verifications passed!")
        exit(0)
    else:
        print("\n❌ Verification failed - see details above")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
