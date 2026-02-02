# Message Data Flow

This document describes the complete end-to-end flow of messages through the OSFeed system, from collection to delivery.

## Overview

Messages flow through six distinct layers:

1. **Collection Layer** - Scheduling and queue management
2. **Fetch Layer** - Rate-limited Telegram API access
3. **Storage Layer** - Bulk insertion and persistence
4. **Translation Layer** - Async batch translation
5. **Deduplication Layer** - Semantic similarity detection
6. **Streaming Layer** - Real-time delivery to users

## Detailed Flow

### 1. Collection Layer

**Component**: `collect_messages_job()` in `backend/app/jobs/collect_messages.py`

**Trigger**: APScheduler runs every 5 minutes

**Process**:
1. Query PostgreSQL for all active channels (`is_active=true`)
2. For each channel, check `last_fetched_at` timestamp
3. If channel hasn't been synced within `telegram_sync_interval_seconds`, enqueue a fetch job
4. For new channels (no `last_fetched_at`), enqueue immediately

**Output**:
- Fetch jobs pushed to Redis queue: `osfeed:fetch_queue`
- Job data includes: `job_id`, `channel_id`, `username`, `days`, `created_at`

**Rate Limiting**: Collection job itself has no rate limit, but respects fetch queue capacity

---

### 2. Fetch Layer

**Components**:
- `fetch_queue.py` - Queue management and worker coordination
- `telegram_client.py` - Telegram API wrapper with rate limiting

#### 2.1 Fetch Queue Workers

**Trigger**: Workers continuously poll Redis queue using `LPOP`

**Process**:
1. Pop job from `osfeed:fetch_queue`
2. Add job to `osfeed:active_fetch_jobs` set (prevents duplicates)
3. Update job status in PostgreSQL: `status='running'`
4. Process job using Telegram client
5. Remove from active set when complete

**Concurrency**: Multiple workers can process different channels simultaneously

#### 2.2 Telegram Client

**Rate Limiting Strategy**:
- **Token Bucket Algorithm** (Redis-backed)
  - Refill rate: `telegram_rate_limit_per_second` tokens/sec
  - Bucket capacity: `telegram_rate_limit_burst`
  - Each API call consumes 1 token
- **FloodWait Handling**:
  - Catch `FloodWaitError` from Telegram
  - Sleep for `error.seconds * telegram_flood_wait_multiplier`
  - Automatic retry after wait period
- **Join Channel Quota**:
  - Daily limit: `telegram_join_channel_daily_limit`
  - Tracked in Redis with 24-hour TTL
  - Prevents hitting Telegram's join restrictions

**Message Fetching Process**:
1. Acquire rate limit token from Redis
2. Call `get_messages()` with parameters:
   - `username`: Channel identifier
   - `limit`: Batch size (default 100)
   - `min_id`: Last known message ID (for incremental sync)
   - `offset_date`: For pagination through history
3. Telegram returns batch of messages (newest first)
4. Extract message data: `id`, `text`, `date`, `media`, `views`, `forwards`
5. Repeat until all new messages fetched or cutoff date reached

**Channel Info Updates**:
- Fetch full channel details: `GetFullChannelRequest`
- Update database fields: `title`, `description`, `subscriber_count`
- Logged but non-blocking (fetch continues on failure)

---

### 3. Storage Layer

**Component**: Bulk insert logic in `_process_fetch_job()`

**Deduplication Strategy**:
1. Query PostgreSQL for `MAX(telegram_message_id)` for channel
2. Only fetch messages with `id > last_known_id`
3. Before insert, check if message already exists:
   ```sql
   SELECT * FROM messages
   WHERE channel_id = ? AND telegram_message_id = ?
   ```
4. Skip existing messages (idempotent operation)

**Bulk Insert Process**:
1. Batch messages (e.g., 100 at a time)
2. Convert Telethon message objects to OSFeed `Message` models:
   - `telegram_message_id`: Original Telegram ID
   - `original_text`: Raw message text
   - `published_at`: Message timestamp
   - `media_type`: photo, video, document, audio (if present)
   - `media_urls`: Extracted URLs (JSON array)
   - `view_count`, `forward_count`: Engagement metrics
   - `needs_translation`: Set to `true` by default
   - `is_duplicate`: Initially `null` (set later by dedup)
3. `db.add_all(messages)` - Single batch commit
4. Update channel's `last_fetched_at` timestamp

**Performance Optimization**:
- Batch size configurable: `telegram_batch_size`
- Reduces database round-trips
- Transaction per batch (not per message)

---

### 4. Translation Layer

**Component**: `translate_pending_messages_job()` in `backend/app/jobs/translate_pending_messages.py`

**Trigger**: APScheduler (separate from collection job)

#### 4.1 Translation Job Selection

**Query**:
```sql
SELECT id, original_text, target_language, source_language,
       published_at, channel_id
FROM messages
WHERE needs_translation = true
  AND (is_duplicate = false OR is_duplicate IS NULL)
ORDER BY published_at DESC
LIMIT 200
```

**Filtering Logic**:
1. **Empty Text Check**: Skip messages with no content
2. **Channel Language Preference**: Check `should_channel_translate(channel_id)`
   - If all users prefer channel's source language, skip translation
   - Optimization: Don't translate if not needed by any subscriber
3. **Trivial Text Detection** (in `llm_translator.py`):
   - URLs only: `^https?://\S+$`
   - Hashtags/mentions: `^[@#]\w+$`
   - Numbers only: `^\d+$`
   - Short words: Configurable skip list
   - Single punctuation: `^[^\w\s]{1,10}$`

#### 4.2 Translation Pool

**Grouping Strategy**:
- Group messages by `(target_language, source_language)` pair
- Enables batch translation for same language combination
- Reduces API calls and improves cache hit rate

**Async Processing**:
```python
async def _translate_group(target_lang, source_lang, items):
    texts = [row.original_text for row in items]
    published_at_list = [row.published_at for row in items]
    results = await run_translation(
        translator.translate_batch(texts, ...)
    )
    return [(id, translated, detected, target, priority), ...]
```

**Priority Routing** (by message age):
- **High Priority**: Messages < `translation_high_priority_hours` old
  - Uses premium model (Gemini Flash or GPT-4o-mini)
  - Ensures fresh content translated quickly
- **Normal Priority**: Messages < `translation_normal_priority_days` old
  - Standard model routing
- **Low Priority**: Older messages
  - May use free/cheaper translation service
- **Skip**: Trivial content, same-language, empty text

#### 4.3 LLM Translator

**Cache Strategy** (Redis-backed):
- **Cache Key**: `SHA256(text)` + `source_lang:target_lang`
- **Adaptive TTL**:
  - Base TTL: `translation_cache_base_ttl` (e.g., 7 days)
  - Hit multiplier: `translation_cache_hit_multiplier` (e.g., 0.1)
  - Formula: `ttl = min(base * (1 + hits * multiplier), max_ttl)`
  - Popular translations stay cached longer
- **Cache Hit Tracking**: Separate Redis counter per cache key

**Translation Process**:
1. Generate cache key for each text
2. `GET` from Redis
3. If miss:
   - Chunk text if > 3500 chars (avoids token limits)
   - Call LLM API with system prompt:
     ```
     OSINT translator. Keep names, dates, URLs, numbers.
     Return only the translation.
     ```
   - Temperature: 0.2 (deterministic output)
   - Store result in Redis with adaptive TTL
4. Track API usage: `record_api_usage()` for cost monitoring

**Model Selection**:
- Primary: `gemini-1.5-flash` (fast, cheap)
- Fallback: `gpt-4o-mini` (if Gemini unavailable)
- Configurable via `openai_model` and `gemini_model` settings

**Batch Translation**:
- Separate texts with `\n\n<<<MSG_SEP>>>\n\n`
- Max batch: 100 messages or 10,000 characters
- Single API call for entire batch
- Split results back to individual messages

#### 4.4 Translation Update

**Database Update**:
```sql
UPDATE messages
SET translated_text = ?,
    source_language = ?,
    target_language = ?,
    needs_translation = false,
    translated_at = NOW(),
    translation_priority = ?
WHERE id = ?
```

**Event Publishing**:
- After commit, publish `message_translated` event
- Includes: `message_id`, `channel_id`, `translated_text`, languages
- Triggers SSE stream to connected clients

---

### 5. Deduplication Layer

**Component**: Qdrant vector database integration

**Process**:
1. **Embedding Generation**:
   - When message is saved/translated, generate text embedding
   - Use sentence transformer model (e.g., `all-MiniLM-L6-v2`)
   - 384-dimensional vector representation

2. **Similarity Search**:
   - Query Qdrant for vectors similar to new message
   - Cosine similarity threshold: `0.85` (configurable)
   - Filter by channel and time window (e.g., last 7 days)

3. **Duplicate Marking**:
   - If similar message found with score > threshold:
     - Set `is_duplicate = true` on new message
     - Store `duplicate_of_id` (reference to original)
   - Duplicates excluded from feed queries

**Use Cases**:
- Cross-posts between channels
- Forwarded messages
- Reposts with minor edits
- Near-identical content

**Performance**:
- Qdrant uses HNSW index (Hierarchical Navigable Small World)
- Sub-millisecond search for millions of vectors
- Scales horizontally with sharding

---

### 6. Streaming Layer

**Component**: Server-Sent Events (SSE) in FastAPI

**Event Types**:
1. **`message_translated`**:
   - Fired when translation completes
   - Payload: Full message object with translation
   - Allows real-time feed updates

2. **`new_message`**:
   - Fired when message first inserted (even before translation)
   - Payload: Message with `original_text` only
   - Preview before translation available

**SSE Implementation**:
```python
@app.get("/api/events/stream")
async def event_stream(user_id: UUID):
    async def event_generator():
        queue = asyncio.Queue()
        # Subscribe to Redis pub/sub
        await subscribe_to_events(user_id, queue)
        while True:
            event = await queue.get()
            yield f"data: {json.dumps(event)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Redis Pub/Sub**:
- Events published to Redis channel: `osfeed:events:{user_id}`
- Multiple backend instances can publish
- SSE connections subscribe to relevant channels
- Automatic reconnection on disconnect

**Frontend Handling**:
- `EventSource` API connects to `/api/events/stream`
- Zustand store updates on incoming events
- React Query cache invalidated for affected queries
- UI auto-refreshes feed without polling

---

## Performance Characteristics

### Throughput
- **Collection**: 1000+ channels per 5-minute cycle
- **Fetch**: 100 messages/sec (respecting rate limits)
- **Translation**: 200 messages per batch job (configurable)
- **Deduplication**: Sub-millisecond per message

### Latency
- **Telegram → Database**: 30-60 seconds (avg)
- **Database → Translated**: 5-30 seconds (depending on priority)
- **Translated → User**: <1 second (SSE push)
- **End-to-end**: 1-2 minutes for fresh messages

### Scalability
- **Fetch Workers**: Horizontal scaling (more workers = more channels)
- **Translation Pool**: Async design supports 100+ concurrent translations
- **Qdrant**: Sharded across multiple nodes for millions of messages
- **SSE**: Sticky sessions required (or use Redis pub/sub for fan-out)

---

## Error Handling

### Fetch Layer Errors
- **FloodWait**: Automatic retry with exponential backoff
- **ChannelPrivate**: Mark channel as inactive, notify admin
- **Rate Limit**: Token bucket blocks until tokens available
- **Network Timeout**: Retry with jitter, max 3 attempts

### Translation Layer Errors
- **API Timeout**: Skip message, retry in next batch
- **Invalid Language**: Log error, mark as `translation_priority='skip'`
- **Quota Exceeded**: Fall back to free translation service
- **Model Error**: Switch to fallback model (Gemini → GPT)

### Database Errors
- **Duplicate Key**: Silently skip (idempotent)
- **Connection Lost**: Retry with backoff, alert if persistent
- **Transaction Timeout**: Reduce batch size, retry

### Qdrant Errors
- **Connection Failed**: Log warning, continue without dedup
- **Embedding Error**: Mark message, retry later
- **Timeout**: Skip deduplication for batch, alert admin

---

## Configuration

### Fetch Settings
```python
telegram_sync_interval_seconds = 300  # 5 minutes
telegram_batch_size = 100
telegram_rate_limit_per_second = 10
telegram_rate_limit_burst = 20
telegram_flood_wait_multiplier = 1.1
telegram_join_channel_daily_limit = 20
```

### Translation Settings
```python
translation_high_priority_hours = 2
translation_normal_priority_days = 7
translation_cache_base_ttl = 604800  # 7 days
translation_cache_max_ttl = 2592000  # 30 days
translation_cache_hit_multiplier = 0.1
translation_skip_trivial = true
translation_skip_same_language = true
```

### Batch Settings
```python
BATCH_SIZE = 200  # Messages per translation job
MAX_BATCH_SIZE = 100  # Messages per LLM batch
MAX_BATCH_CHARS = 10000  # Character limit per batch
```

---

## Monitoring

### Key Metrics
- **Fetch Queue Depth**: Redis list length (`LLEN osfeed:fetch_queue`)
- **Active Fetch Jobs**: Set size (`SCARD osfeed:active_fetch_jobs`)
- **Translation Backlog**: Count of `needs_translation=true`
- **Cache Hit Rate**: `cache_hits / (cache_hits + cache_misses)`
- **API Costs**: `sum(api_usage.cost)` per provider
- **Duplicate Rate**: `is_duplicate=true / total_messages`

### Logs
- **Fetch**: Job start/complete, message counts, errors
- **Translation**: Batch size, cache stats, API calls, timing
- **Rate Limiting**: Token acquisition, FloodWait events, quotas
- **Errors**: Stack traces, retry attempts, failed channels

### Alerts
- Fetch queue depth > 100 (backlog building)
- Translation backlog > 5000 (need more capacity)
- Cache hit rate < 30% (poor cache effectiveness)
- FloodWait > 300s (approaching ban risk)
- Daily API cost > $50 (budget threshold)

---

## Future Optimizations

### Planned Improvements
1. **Intelligent Batching**: Group messages by topic for better cache hits
2. **Predictive Fetch**: ML model to predict channel activity, pre-fetch
3. **Edge Caching**: CDN for translated messages, reduce DB load
4. **Compression**: Gzip SSE stream, reduce bandwidth
5. **Smart Dedup**: Use message metadata (forwards, quotes) before vector search

### Under Consideration
- WebSocket alternative to SSE for bi-directional communication
- GraphQL subscriptions for more flexible event filtering
- Multi-language translation (one message → many languages)
- Federated Qdrant across regions for lower latency
