-- ============================================================================
-- Database Index Verification Script
-- Purpose: Verify that source_language indexes exist and are being used
-- ============================================================================

\echo '=========================================================================='
\echo 'Database Index Verification - Source Language Indexes'
\echo '=========================================================================='
\echo ''

-- Step 1: Check if indexes exist
\echo 'Step 1: Checking if required indexes exist...'
\echo '--------------------------------------------------------------------------'
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'messages'
AND indexname IN ('ix_messages_source_language', 'ix_messages_channel_published_lang')
ORDER BY indexname;

\echo ''
\echo 'Expected: 2 rows showing both indexes'
\echo ''

-- Step 2: Show table size
\echo 'Step 2: Checking messages table size...'
\echo '--------------------------------------------------------------------------'
SELECT
    COUNT(*) as total_messages,
    COUNT(DISTINCT channel_id) as distinct_channels,
    COUNT(DISTINCT source_language) as distinct_languages,
    MIN(published_at) as oldest_message,
    MAX(published_at) as newest_message
FROM messages;

\echo ''
\echo 'Note: If total_messages < 1000, PostgreSQL may prefer Sequential Scan'
\echo ''

-- Step 3: Get sample channel IDs for testing
\echo 'Step 3: Getting sample channel IDs...'
\echo '--------------------------------------------------------------------------'
SELECT id, title, username
FROM channels
WHERE is_active = true
LIMIT 3;

\echo ''
\echo 'Copy channel IDs for the next query'
\echo ''

-- Step 4: EXPLAIN query (template - replace UUIDs)
\echo 'Step 4: Run EXPLAIN ANALYZE on collections stats query'
\echo '--------------------------------------------------------------------------'
\echo 'Replace the UUIDs below with actual channel IDs from Step 3:'
\echo ''
\echo 'EXPLAIN (ANALYZE, BUFFERS, VERBOSE)'
\echo 'SELECT'
\echo '    DATE(published_at) AS day,'
\echo '    source_language,'
\echo '    COUNT(*) AS count,'
\echo '    SUM(CASE WHEN is_duplicate = true THEN 1 ELSE 0 END) AS dup_count'
\echo 'FROM messages'
\echo 'WHERE channel_id IN ('
\echo '    ''00000000-0000-0000-0000-000000000001''::uuid,'
\echo '    ''00000000-0000-0000-0000-000000000002''::uuid'
\echo ')'
\echo 'GROUP BY DATE(published_at), source_language;'
\echo ''
\echo '--------------------------------------------------------------------------'
\echo ''

-- Step 5: Index usage statistics
\echo 'Step 5: Checking index usage statistics...'
\echo '--------------------------------------------------------------------------'
SELECT
    indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as size
FROM pg_stat_user_indexes
WHERE tablename = 'messages'
AND indexname IN ('ix_messages_source_language', 'ix_messages_channel_published_lang')
ORDER BY indexname;

\echo ''
\echo 'Note: idx_scan = 0 if indexes haven''t been used yet (expected for new indexes)'
\echo ''

-- Step 6: All message table indexes
\echo 'Step 6: All indexes on messages table...'
\echo '--------------------------------------------------------------------------'
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'messages'
ORDER BY indexname;

\echo ''
\echo '=========================================================================='
\echo 'Verification Complete'
\echo '=========================================================================='
\echo ''
\echo 'Next steps:'
\echo '1. Verify both indexes exist (Step 1)'
\echo '2. Note the table size (Step 2)'
\echo '3. Run EXPLAIN ANALYZE with real channel IDs (Step 4)'
\echo '4. Look for "Index Scan" or "Bitmap Index Scan" in the output'
\echo '5. Document results in backend/docs/query-plan-verification.md'
\echo ''
