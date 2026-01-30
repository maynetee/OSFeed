# Database Indexes Audit for Messages Table

**Audit Date:** 2026-01-30
**Purpose:** Audit existing message indexes against query patterns to identify optimization opportunities

---

## 1. Existing Indexes from Migrations

### Initial Schema (be3f078b6cf1)
Created basic indexes for the messages table:

| Index Name | Columns | Type | Notes |
|------------|---------|------|-------|
| `ix_messages_channel_id` | `channel_id` | B-tree | Single column |
| `ix_messages_published_at` | `published_at` | B-tree | Single column |
| `ix_messages_is_duplicate` | `is_duplicate` | B-tree | Single column |
| `ix_messages_channel_published` | `channel_id, published_at` | B-tree | Composite (2 cols) |
| `ix_messages_channel_telegram_id` | `channel_id, telegram_message_id` | B-tree UNIQUE | Deduplication constraint |
| `ix_messages_duplicate_group` | `duplicate_group_id` | B-tree | Partial index (WHERE duplicate_group_id IS NOT NULL) |

### Cursor Index Migration (c2f4a9d1e7b3)
Added support for cursor-based pagination:

| Index Name | Columns | Type | Notes |
|------------|---------|------|-------|
| `ix_messages_channel_published_id` | `channel_id, published_at, id` | B-tree | Composite (3 cols) - cursor pagination |

### Translation/Stats Indexes (e1a2b3c4d5f6)
Added indexes for translation jobs and stats queries:

| Index Name | Columns | Type | Notes |
|------------|---------|------|-------|
| `ix_messages_translation_query` | `channel_id, needs_translation, translation_priority` | B-tree | Translation job optimization |
| `ix_messages_stats_query` | `published_at, is_duplicate` | B-tree | Stats queries with date ranges |

### Full-Text Search Indexes (f2b3c4d5e6a7)
Added GIN indexes for text search (PostgreSQL only):

| Index Name | Columns | Type | Notes |
|------------|---------|------|-------|
| `ix_messages_original_text_trgm` | `original_text` | GIN (pg_trgm) | ILIKE pattern matching |
| `ix_messages_translated_text_trgm` | `translated_text` | GIN (pg_trgm) | ILIKE pattern matching |

### Performance Indexes (a1b2c3d4e5f6)
Added composite index for filtered timeline queries:

| Index Name | Columns | Type | Notes |
|------------|---------|------|-------|
| `ix_messages_channel_published_dedup` | `channel_id, published_at, is_duplicate` | B-tree | Collection endpoints |

---

## 2. Indexes Declared in Model (backend/app/models/message.py)

The Message model `__table_args__` declares the following indexes:

```python
Index("ix_messages_channel_telegram_id", "channel_id", "telegram_message_id", unique=True)
Index("ix_messages_channel_published", "channel_id", "published_at")
Index("ix_messages_channel_published_id", "channel_id", "published_at", "id")
Index("ix_messages_duplicate_group", "duplicate_group_id", postgresql_where=duplicate_group_id.isnot(None))
Index("ix_messages_translation_query", "channel_id", "needs_translation", "translation_priority")
Index("ix_messages_stats_query", "published_at", "is_duplicate")
Index("ix_messages_channel_published_dedup", "channel_id", "published_at", "is_duplicate")
Index("ix_messages_text_search", "original_text", "translated_text", postgresql_using="gin", postgresql_ops={"original_text": "gin_trgm_ops", "translated_text": "gin_trgm_ops"})
```

**Note:** The model also declares single-column indexes via `index=True`:
- `channel_id` (via ForeignKey)
- `needs_translation`
- `is_duplicate`
- `duplicate_group_id`
- `published_at`

---

## 3. Query Patterns from API Files

### 3.1 Messages API (backend/app/api/messages.py)

#### List Messages Endpoint (`GET /api/messages`)
**Primary Query Pattern:**
```python
SELECT * FROM messages
JOIN channels ON messages.channel_id = channels.id
JOIN user_channels ON ...
WHERE channel_id IN (...)
  AND published_at >= ?
  AND published_at <= ?
ORDER BY published_at DESC, id DESC
LIMIT ? OFFSET ?
```

**Cursor-Based Pagination:**
```python
WHERE (published_at, id) < (?, ?)
ORDER BY published_at DESC, id DESC
```

**Index Coverage:** ✅ **COVERED** by `ix_messages_channel_published_id`

---

#### Stream Messages Endpoint (`GET /api/messages/stream`)
**Historical Stream Pattern:**
```python
SELECT * FROM messages
JOIN channels ON messages.channel_id = channels.id
JOIN user_channels ON ...
WHERE channel_id IN (...)
  AND published_at >= ?
  AND published_at <= ?
ORDER BY published_at DESC, id DESC
LIMIT ? OFFSET ?
```

**Realtime Polling Pattern:**
```python
WHERE (published_at, id) > (?, ?)
ORDER BY published_at ASC, id ASC
LIMIT 50
```

**Index Coverage:** ✅ **COVERED** by `ix_messages_channel_published_id`

---

#### Search Messages Endpoint (`GET /api/messages/search`)
**PostgreSQL Pattern:**
```python
SELECT * FROM messages
JOIN channels ON messages.channel_id = channels.id
JOIN user_channels ON ...
WHERE (original_text % 'search_term' OR translated_text % 'search_term')
  AND channel_id IN (...)
  AND published_at >= ?
  AND published_at <= ?
ORDER BY published_at DESC, id DESC
```

**Index Coverage:**
- ✅ **COVERED** Text search by `ix_messages_original_text_trgm` and `ix_messages_translated_text_trgm`
- ✅ **COVERED** Ordering by `ix_messages_channel_published_id`
- ⚠️ **POTENTIAL OPTIMIZATION:** Multi-column GIN index could combine text search with channel filtering

---

#### Translate Messages Endpoint (`POST /api/messages/translate`)
**Query Pattern:**
```python
SELECT id, original_text, published_at FROM messages
JOIN channels ON messages.channel_id = channels.id
JOIN user_channels ON ...
WHERE needs_translation = TRUE
  AND channel_id = ?
```

**Cache Lookup Pattern:**
```python
SELECT * FROM message_translations
WHERE message_id IN (...)
  AND target_lang = ?
```

**Index Coverage:**
- ✅ **COVERED** by `ix_messages_translation_query` (channel_id, needs_translation, translation_priority)
- ✅ **COVERED** MessageTranslation by `ix_message_translations_lookup` (message_id, target_lang)

---

#### Export Endpoints (CSV, HTML, PDF)
**Query Pattern:**
```python
SELECT messages.*, channels.* FROM messages
JOIN channels ON messages.channel_id = channels.id
JOIN user_channels ON ...
WHERE channel_id = ? OR channel_id IN (...)
  AND published_at >= ?
  AND published_at <= ?
ORDER BY published_at DESC
LIMIT ? OFFSET ?
```

**Index Coverage:** ✅ **COVERED** by `ix_messages_channel_published` or `ix_messages_channel_published_id`

---

#### Get Message Media (`GET /api/messages/{message_id}/media`)
**Query Pattern:**
```python
SELECT * FROM messages
JOIN channels ON messages.channel_id = channels.id
JOIN user_channels ON ...
WHERE messages.id = ?
```

**Index Coverage:** ✅ **COVERED** by primary key (messages.id)

---

### 3.2 Collections API (backend/app/api/collections.py)

#### Collection Overview/Compare Endpoints
**Query Pattern:**
```python
SELECT channel_id, COUNT(*) FROM messages
WHERE channel_id IN (...)
  AND published_at >= ?
GROUP BY channel_id
```

**Duplicate Count Pattern:**
```python
SELECT channel_id, COUNT(*) FROM messages
WHERE channel_id IN (...)
  AND published_at >= ?
  AND is_duplicate = TRUE
GROUP BY channel_id
```

**Index Coverage:**
- ✅ **COVERED** by `ix_messages_channel_published` for filtering
- ⚠️ **SUBOPTIMAL:** Counting with `is_duplicate` filter could benefit from `ix_messages_channel_published_dedup`

---

#### Collection List Endpoint
**Query Pattern:**
```python
SELECT messages.*, channels.* FROM messages
JOIN channels ON messages.channel_id = channels.id
WHERE channel_id IN (...)
  AND published_at >= ?
  AND published_at <= ?
  AND is_duplicate = FALSE
ORDER BY published_at DESC
```

**Index Coverage:** ✅ **COVERED** by `ix_messages_channel_published_dedup` (channel_id, published_at, is_duplicate)

---

### 3.3 Stats API (backend/app/api/stats.py)

#### Dashboard Stats
**Total Messages Query:**
```python
SELECT COUNT(*) FROM messages
JOIN channels ON messages.channel_id = channels.id
JOIN user_channels ON ...
```

**24h Messages Query:**
```python
SELECT COUNT(*) FROM messages
JOIN channels ON messages.channel_id = channels.id
JOIN user_channels ON ...
WHERE published_at >= ?
```

**Duplicates Query:**
```python
SELECT COUNT(*) FROM messages
JOIN channels ON messages.channel_id = channels.id
JOIN user_channels ON ...
WHERE published_at >= ?
  AND is_duplicate = TRUE
```

**Index Coverage:**
- ✅ **COVERED** Date filtering by `ix_messages_published_at`
- ✅ **COVERED** Date + duplicate filtering by `ix_messages_stats_query` (published_at, is_duplicate)

---

#### Activity Stats (Messages by Period)
**Query Pattern:**
```python
SELECT COUNT(*) FROM messages
JOIN channels ON messages.channel_id = channels.id
JOIN user_channels ON ...
WHERE channel_id IN (...)
  AND published_at >= ?
  AND published_at <= ?
  AND is_duplicate = FALSE
```

**Index Coverage:** ✅ **COVERED** by `ix_messages_channel_published_dedup` (channel_id, published_at, is_duplicate)

---

#### Top Channels Query
**Query Pattern:**
```python
SELECT channels.id, channels.title, COUNT(messages.id)
FROM channels
JOIN messages ON messages.channel_id = channels.id
JOIN user_channels ON ...
WHERE channel_id IN (...)
  AND published_at >= ?
  AND published_at <= ?
GROUP BY channels.id, channels.title
ORDER BY COUNT(messages.id) DESC
```

**Index Coverage:** ✅ **COVERED** by `ix_messages_channel_published`

---

#### Per-Channel Message Stats
**Query Pattern:**
```python
SELECT channel_id, COUNT(*) FROM messages
WHERE channel_id IN (...)
  AND published_at >= ?
GROUP BY channel_id
```

**Index Coverage:** ✅ **COVERED** by `ix_messages_channel_published`

---

## 4. Analysis and Recommendations

### 4.1 Index Coverage Summary

| Query Pattern | Current Index | Status |
|--------------|---------------|--------|
| Timeline pagination (channel + date + id) | `ix_messages_channel_published_id` | ✅ Optimal |
| Collection timeline (channel + date + dedup) | `ix_messages_channel_published_dedup` | ✅ Optimal |
| Translation jobs (channel + needs_translation) | `ix_messages_translation_query` | ✅ Optimal |
| Stats queries (date + dedup) | `ix_messages_stats_query` | ✅ Optimal |
| Full-text search | `ix_messages_*_text_trgm` | ✅ Optimal |
| Message deduplication | `ix_messages_channel_telegram_id` | ✅ Optimal |
| Duplicate grouping | `ix_messages_duplicate_group` | ✅ Optimal |

### 4.2 Potential Optimizations

#### 4.2.1 Multi-Channel Queries (Low Priority)
**Query Pattern:**
```sql
WHERE channel_id IN (id1, id2, ..., idN)
  AND published_at >= ?
  AND published_at <= ?
ORDER BY published_at DESC
```

**Current Index:** `ix_messages_channel_published`
**Status:** ⚠️ **ADEQUATE** - Works well for small channel lists, but IN clause can be less efficient for large lists
**Recommendation:** Consider a covering index if multi-channel queries become a bottleneck

---

#### 4.2.2 Source Language Analytics (Currently NOT Indexed)
**Potential Query Pattern:**
```sql
SELECT source_language, COUNT(*) FROM messages
WHERE published_at >= ?
GROUP BY source_language
```

**Current Index:** ❌ **NONE** - No index on `source_language`
**Spec Rationale:** "source_language for analytics" mentioned in spec.md
**Recommendation:** ⚠️ **CONSIDER ADDING** if language analytics queries are frequent

**Proposed Index:**
```python
Index("ix_messages_source_language_published", "source_language", "published_at")
```

---

#### 4.2.3 Media Queries (Currently NOT Indexed)
**Potential Query Pattern:**
```sql
SELECT * FROM messages
WHERE media_type = 'photo' OR media_type = 'video'
  AND channel_id = ?
ORDER BY published_at DESC
```

**Current Index:** ❌ **NONE** - No index on `media_type`
**Status:** Not currently used in API endpoints
**Recommendation:** ⚠️ **LOW PRIORITY** - Only add if media filtering becomes a feature

---

### 4.3 Recommended Actions

#### ✅ NO IMMEDIATE ACTION REQUIRED
The current index strategy is **comprehensive and well-optimized** for all documented query patterns in the API.

#### ⚠️ FUTURE CONSIDERATIONS

1. **Source Language Analytics Index** (Spec Priority)
   - **When:** If language distribution analytics are added
   - **Index:** `CREATE INDEX ix_messages_source_language_published ON messages(source_language, published_at)`
   - **Benefit:** Fast aggregation queries for language statistics

2. **Monitoring Recommendations**
   - Monitor slow query logs for `channel_id IN (...)` patterns with large lists
   - Track index usage statistics to identify unused indexes
   - Monitor index bloat and perform REINDEX if needed

3. **PostgreSQL-Specific Optimizations**
   - Current GIN indexes for full-text search are optimal
   - Consider `pg_stat_user_indexes` to verify index usage
   - Consider `ANALYZE` after bulk inserts for query planner accuracy

---

## 5. Index Maintenance Notes

### 5.1 Index Size Considerations
- **GIN indexes** (`ix_messages_*_text_trgm`) are the largest and most maintenance-intensive
- **Composite indexes** with 3+ columns may become bloated over time
- **Partial indexes** (e.g., `ix_messages_duplicate_group`) are efficient for sparse data

### 5.2 Write Performance Impact
- Total indexes on messages table: **13 indexes** (including PKs and FKs)
- Each INSERT/UPDATE must update all applicable indexes
- Trade-off: Excellent read performance vs. moderate write overhead
- **Recommendation:** Acceptable for read-heavy workload (message fetching >> message ingestion)

### 5.3 Index Usage Verification (PostgreSQL)
```sql
-- Check index usage statistics
SELECT
    schemaname, tablename, indexname,
    idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'messages'
ORDER BY idx_scan DESC;

-- Check index sizes
SELECT
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass))
FROM pg_indexes
WHERE tablename = 'messages';
```

---

## 6. Conclusion

The messages table has a **well-designed and comprehensive indexing strategy** that covers:
- ✅ All documented query patterns in API endpoints
- ✅ Cursor-based pagination optimization
- ✅ Full-text search (PostgreSQL)
- ✅ Translation job queries
- ✅ Stats and analytics queries
- ✅ Deduplication and grouping

**The only gap identified from the spec** is the lack of an index on `source_language` for analytics queries. This should be added if language distribution analytics become a requirement.

**Recommendation:** Proceed with adding the `source_language` index as specified in the spec, then move to the next phase of the implementation plan.
