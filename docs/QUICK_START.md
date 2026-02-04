# Quick Start Guide

**Read this in 5 minutes to understand how OSFeed works.**

## What is OSFeed?

OSFeed is a Telegram OSINT platform that automatically:
1. **Collects** messages from Telegram channels
2. **Translates** them into your preferred language
3. **Removes duplicates** using AI-powered semantic matching
4. **Generates daily digests** of the most important content

Think of it as an intelligent RSS reader specifically for Telegram channels with built-in translation and deduplication.

## System Architecture at a Glance

```
User Browser (React)
        ↓
   Backend API (FastAPI)
        ↓
   ┌────┴────┬─────────┬────────┐
   ↓         ↓         ↓        ↓
PostgreSQL  Qdrant   Redis  Telegram API
(messages) (vectors) (cache) (source)
```

### Core Components

- **Frontend**: React 18 + TypeScript + Tailwind CSS (Vite dev server)
- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + APScheduler
- **Databases**:
  - PostgreSQL: Main data storage
  - Qdrant: Vector search for deduplication
  - Redis: Caching & queue management
- **External APIs**:
  - Telegram API: Message collection
  - LLM APIs: Translation (Gemini Flash, GPT-4o-mini)

## How Messages Flow Through the System

### 1. Collection (Every 5 Minutes)
- Background job queries all active channels
- Channels needing sync are added to Redis fetch queue
- Respects Telegram rate limits (token bucket algorithm)

### 2. Fetching (Async Workers)
- Workers pull jobs from Redis queue
- Fetch new messages from Telegram via rate-limited client
- Handle flood waits and daily join limits automatically

### 3. Storage (Bulk Insert)
- Messages saved to PostgreSQL in batches
- Idempotent: Duplicate telegram_message_id silently skipped
- Updates channel metadata (title, subscriber count, last_fetched_at)

### 4. Translation (Async Batch Processing)
- Separate background job finds `needs_translation=true` messages
- Groups messages by language pair for efficient batch translation
- **Smart caching**: Redis-backed with adaptive TTL (popular translations persist longer)
- **Priority routing**:
  - Recent messages (<24h): Premium models (GPT-4o-mini)
  - Normal messages: Standard models (Gemini Flash)
  - Skips trivial content (URLs only, single emojis, etc.)

### 5. Deduplication (Vector Similarity)
- Generates embeddings for message content
- Stores vectors in Qdrant
- Compares cosine similarity (threshold: configurable)
- Marks duplicates with `is_duplicate=true` and links to original

### 6. Delivery (Real-time WebSocket + REST)
- Frontend fetches messages via `/api/messages` (paginated, filtered)
- WebSocket pushes new messages to connected clients
- Daily digest job aggregates non-duplicate messages into summaries

## Key Design Decisions

1. **Why User Account (not Bot API)?**
   - Access to private channels
   - No bot restrictions
   - Full message history

2. **Why Vector DB for Deduplication?**
   - Semantic matching catches paraphrased duplicates
   - Language-agnostic (works on translations)
   - Scalable to millions of messages

3. **Why Multi-LLM Strategy?**
   - Cost optimization (cheap models for bulk, premium for priority)
   - Fallback on failure (Gemini → GPT-4o-mini)
   - Model-specific strengths (speed vs. accuracy)

4. **Why Redis for Everything?**
   - Queue: Fast LPOP/RPUSH for job queue
   - Cache: LRU eviction for translation results
   - Rate Limiting: Atomic INCR operations for token bucket

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Telegram API credentials (api_id, api_hash from my.telegram.org)
- LLM API keys (OpenAI and/or Google Gemini)

### Quick Setup
```bash
# 1. Clone and configure
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# 2. Start all services
docker-compose up -d

# 3. Initialize database
docker-compose exec backend alembic upgrade head

# 4. Setup Telegram session (interactive)
docker-compose exec backend python -m app.utils.create_session

# 5. Access application
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

### First Steps
1. **Add a channel**: POST to `/api/channels` with Telegram username
2. **Wait for collection**: Jobs run every 5 minutes (or trigger manually)
3. **Check messages**: GET `/api/messages?channel_id=123`
4. **View digests**: GET `/api/digests` for daily summaries

## Directory Structure

```
OSFeed/
├── frontend/          # React app (Vite)
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── pages/       # Route pages
│   │   ├── store/       # Zustand state
│   │   └── services/    # API clients
│   └── public/
├── backend/           # FastAPI app
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── models/      # SQLAlchemy models
│   │   ├── services/    # Business logic
│   │   ├── jobs/        # Background jobs
│   │   ├── integrations/ # External APIs
│   │   └── utils/       # Helpers
│   └── alembic/       # Database migrations
└── docs/              # Documentation (you are here!)
```

## Where to Learn More

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Comprehensive system design details
- **[DATA_FLOW.md](./DATA_FLOW.md)** - Complete message processing pipeline
- **[API Documentation](http://localhost:8000/docs)** - Interactive OpenAPI docs (when running)
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Development workflow and standards

## Common Tasks

### Add a New Background Job
1. Create job function in `backend/app/jobs/your_job.py`
2. Register in `backend/app/main.py` scheduler with cron/interval
3. Job automatically runs in production

### Add a New API Endpoint
1. Create route in `backend/app/api/endpoints/`
2. Define Pydantic request/response models
3. Implement service logic in `backend/app/services/`
4. Auto-documented at `/docs`

### Add a New Frontend Page
1. Create component in `frontend/src/pages/YourPage.tsx`
2. Register route in `frontend/src/App.tsx`
3. Add navigation link in header/sidebar
4. Route lazy-loads automatically

## Troubleshooting

- **Messages not fetching?** Check `docker-compose logs backend` for rate limit or auth errors
- **Translations not working?** Verify LLM API keys in `.env` and check Redis connection
- **Duplicates not detected?** Ensure Qdrant is running and embeddings are generating
- **Frontend not connecting?** Check CORS settings and WebSocket proxy config

## Performance at Scale

Current system handles:
- **100+ channels** with 5-minute sync intervals
- **10,000+ messages/day** with batch translation
- **1M+ vectors** in Qdrant for deduplication
- **<500ms API response** times with Redis caching

For production optimization, see [ARCHITECTURE.md - Scalability Considerations](./ARCHITECTURE.md#scalability-considerations).

---

**You're now ready to explore OSFeed!** Start with the API docs at `/docs` or dive into the code in `backend/app/` and `frontend/src/`.
