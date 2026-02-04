# GIN Index Verification Guide

## Overview

This guide explains how to verify that PostgreSQL is using the GIN trigram index on the `translated_text` column after removing the COALESCE wrapper.

## What Was Changed

**Before (with COALESCE):**
```python
func.coalesce(Message.translated_text, literal("")).op("%")(q)
```

**After (without COALESCE):**
```python
Message.translated_text.op("%")(q)
```

The COALESCE wrapper prevented PostgreSQL from using the GIN trigram index on the `translated_text` column because:
- PostgreSQL cannot use functional indexes when the column is wrapped in a function
- NULL values naturally don't match the trigram similarity operator `%`, so COALESCE is unnecessary

## Prerequisites

1. **PostgreSQL database must be running**
   ```bash
   # Start the infrastructure services
   docker-compose -f docker-compose.infra.yml up -d postgres

   # Wait for PostgreSQL to be ready
   docker exec osfeed-postgres pg_isready -U osfeed_user -d osfeed_db
   ```

2. **Database must have the GIN index created**

   The index `ix_messages_text_search` should already exist (defined in `app/models/message.py`):
   ```python
   Index(
       "ix_messages_text_search",
       "original_text",
       "translated_text",
       postgresql_using="gin",
       postgresql_ops={"original_text": "gin_trgm_ops", "translated_text": "gin_trgm_ops"},
   )
   ```

3. **Python environment set up**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

## Running the Verification

### Automated Verification Script

Run the provided verification script:

```bash
cd backend
python verify_gin_index.py
```

### Expected Output

The script will:
1. Connect to PostgreSQL
2. Generate a search query using `build_search_query()`
3. Run `EXPLAIN ANALYZE` on the query
4. Analyze the query plan

**Successful verification should show:**
- ✅ "Query uses an index"
- Evidence of GIN index usage or Bitmap Index Scan
- No sequential scan on translated_text (or acceptable if table is small)

**Example successful output:**
```
======================================================================
GIN Index Usage Verification
======================================================================

Database: PostgreSQL at localhost:5432
Database Name: osfeed_db

Search term: 'test'

Generated SQL Query:
----------------------------------------------------------------------
SELECT messages.id, messages.channel_id, ...
FROM messages
WHERE messages.original_text % 'test' OR messages.translated_text % 'test'
----------------------------------------------------------------------

Query Execution Plan:
----------------------------------------------------------------------
Bitmap Heap Scan on messages  (cost=...)
  Recheck Cond: ((original_text % 'test'::text) OR (translated_text % 'test'::text))
  ->  BitmapOr  (cost=...)
        ->  Bitmap Index Scan on ix_messages_text_search  (cost=...)
              Index Cond: (original_text % 'test'::text)
        ->  Bitmap Index Scan on ix_messages_text_search  (cost=...)
              Index Cond: (translated_text % 'test'::text)
----------------------------------------------------------------------

Analysis:
----------------------------------------------------------------------
✅ PASS: Query uses an index
   - GIN index detected in query plan
   - Bitmap Index Scan detected (efficient for GIN)
```

### Manual Verification (Alternative)

If you prefer to verify manually:

1. **Connect to PostgreSQL:**
   ```bash
   docker exec -it osfeed-postgres psql -U osfeed_user -d osfeed_db
   ```

2. **Ensure pg_trgm extension is enabled:**
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   ```

3. **Check the index exists:**
   ```sql
   \di ix_messages_text_search
   ```

4. **Run EXPLAIN ANALYZE on a search query:**
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM messages
   WHERE original_text % 'test' OR translated_text % 'test';
   ```

5. **Verify the output shows index usage:**
   - Look for "Bitmap Index Scan on ix_messages_text_search"
   - Look for "Index Scan using ix_messages_text_search"
   - **Should NOT see** "Seq Scan on messages" for the translated_text condition

## Understanding the Results

### Small Tables (<1000 rows)
- PostgreSQL may still use Sequential Scan even with the index
- This is a **query planner optimization** - seq scan can be faster for small tables
- The important thing is that the index **can** be used when the table grows

### Large Tables (>1000 rows)
- Should see Bitmap Index Scan or Index Scan
- This proves the GIN index is being used effectively
- Significant performance improvement over sequential scan

### Why This Matters

With the COALESCE wrapper removed:
- **Before:** PostgreSQL could NOT use the index on `translated_text` (forced seq scan)
- **After:** PostgreSQL CAN use the index on `translated_text` (uses index when beneficial)

Even if the current table is small and uses a seq scan, the fix ensures:
- The index will be used as the table grows
- Future performance is optimized
- No degradation for small tables (PostgreSQL chooses the best plan)

## Troubleshooting

### "Database connection failed"
- Ensure PostgreSQL container is running
- Check `.env` file has correct database credentials
- Verify network connectivity

### "Index not found"
- Run migrations: `alembic upgrade head`
- Or manually create index (see Prerequisites)

### "Import errors"
- Ensure you're in the backend directory
- Install dependencies: `pip install -r requirements.txt`

### "Sequential Scan still appears"
- Check table size: `SELECT COUNT(*) FROM messages;`
- If <1000 rows, this is expected behavior
- The key improvement is that the index **can** be used when needed

## References

- PostgreSQL GIN Indexes: https://www.postgresql.org/docs/current/gin.html
- pg_trgm Extension: https://www.postgresql.org/docs/current/pgtrgm.html
- Original Issue: Line 40 in `app/services/message_search_service.py`
- Fixed Code: `Message.translated_text.op("%")(q)` without COALESCE wrapper
