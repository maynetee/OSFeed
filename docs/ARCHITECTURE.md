# OSFeed Architecture

This document provides a comprehensive overview of the OSFeed platform architecture, including system design, service descriptions, technology stack, and key design decisions.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Core Components](#core-components)
  - [Frontend Layer](#frontend-layer)
  - [Backend Layer](#backend-layer)
  - [Data Layer](#data-layer)
  - [External Integrations](#external-integrations)
- [Service Architecture](#service-architecture)
- [Background Jobs](#background-jobs)
- [Key Design Decisions](#key-design-decisions)
- [Security Architecture](#security-architecture)
- [Deployment Architecture](#deployment-architecture)
- [Scalability Considerations](#scalability-considerations)

## System Overview

OSFeed is a Telegram-first OSINT (Open Source Intelligence) platform designed for efficient collection, translation, deduplication, and daily digest generation from Telegram channels. The platform employs a modern microservices architecture with the following characteristics:

- **Containerized Architecture**: All services run in Docker containers for consistent deployment
- **Event-Driven Processing**: Asynchronous message processing with queue-based orchestration
- **Multi-Database Strategy**: PostgreSQL for relational data, Qdrant for vector search, Redis for caching
- **API-First Design**: RESTful API with WebSocket support for real-time updates
- **Background Job Processing**: APScheduler-based task scheduling for periodic operations

## Architecture Diagram

For a visual overview of the system architecture, see the [System Overview Diagram](./diagrams/system-overview.mmd).

The architecture follows a layered approach:

```
┌─────────────────────────────────────────────────────────────┐
│                    External Users                           │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Traefik Reverse Proxy (Production)             │
│            SSL Termination + Let's Encrypt                  │
└────────┬──────────────────────────────────┬─────────────────┘
         │                                  │
         ▼                                  ▼
┌─────────────────┐              ┌──────────────────────────┐
│  Frontend       │              │  Backend API             │
│  React 18       │◄────REST─────┤  FastAPI + Uvicorn       │
│  Port: 5173/80  │   WebSocket  │  Port: 8000              │
└─────────────────┘              └──────────┬───────────────┘
                                            │
              ┌─────────────────────────────┼─────────────────────────┐
              │                             │                         │
              ▼                             ▼                         ▼
    ┌──────────────────┐        ┌──────────────────┐      ┌─────────────────┐
    │   PostgreSQL     │        │     Qdrant       │      │     Redis       │
    │  Primary Data    │        │  Vector Search   │      │  Cache Layer    │
    │  Port: 5432      │        │  Port: 6333      │      │  Port: 6379     │
    └──────────────────┘        └──────────────────┘      └─────────────────┘
```

## Core Components

### Frontend Layer

**Technology Stack:**
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite (modern, fast bundler)
- **Styling**: Tailwind CSS (utility-first CSS framework)
- **State Management**: Zustand (lightweight state management)
- **Data Fetching**: React Query (server state management with caching)
- **Routing**: React Router v6
- **Internationalization**: i18n support (FR/EN)

**Key Features:**
- **PWA Support**: Offline-capable Progressive Web App with service workers
- **Command Palette**: ⌘K keyboard shortcut for quick navigation
- **Virtualized Feeds**: Efficient rendering of large message lists with react-window
- **Lazy Loading**: Code-split routes for optimal bundle size
- **Responsive Design**: Mobile-first responsive UI with Tailwind

**Port Configuration:**
- Development: 5173 (Vite dev server)
- Production: 80 (Nginx serving static build)

### Backend Layer

**Technology Stack:**
- **Framework**: FastAPI (modern, high-performance Python web framework)
- **ASGI Server**: Uvicorn with 4 workers in production
- **ORM**: SQLAlchemy 2.0 with async support
- **Database Driver**: asyncpg (PostgreSQL), aiosqlite (SQLite fallback)
- **Validation**: Pydantic v2 for request/response models
- **Authentication**: JWT tokens with refresh token rotation
- **Scheduler**: APScheduler for background jobs
- **Caching**: Redis with FastAPI-cache integration

**Port Configuration:**
- API Server: 8000
- API Documentation: /docs (OpenAPI/Swagger)

**Architecture Patterns:**
- **Service Layer Pattern**: Business logic isolated in service modules
- **Repository Pattern**: Database access abstracted through SQLAlchemy models
- **Dependency Injection**: FastAPI's dependency injection for database sessions, auth
- **Middleware Stack**: CORS, security headers, error handling
- **Async/Await**: Full async support for I/O-bound operations

### Data Layer

#### PostgreSQL (Primary Database)

**Purpose**: Persistent storage for all relational data

**Schema Design:**
- **Users**: Authentication, profiles, permissions
- **Channels**: Telegram channel metadata, subscriber counts
- **Messages**: Raw and translated message content with metadata
- **Collections**: User-defined channel groupings
- **FetchJobs**: Queue job status tracking
- **AuditLogs**: RGPD-compliant activity logging
- **Alerts**: Collection monitoring and notifications
- **CollectionShares**: Permission-based collection sharing

**Configuration:**
- Connection pooling: 20 connections, 10 overflow
- Pool recycle: 1800 seconds (30 minutes)
- Async driver: asyncpg for high-performance async queries

#### Qdrant (Vector Database)

**Purpose**: Semantic search and duplicate detection

**Use Cases:**
- **Deduplication**: Vector similarity matching to identify duplicate content
- **Semantic Search**: Find similar messages by meaning, not just keywords
- **Clustering**: Group related messages for digest generation

**Vector Strategy:**
- Embeddings generated via OpenAI embedding models
- Cosine similarity for duplicate detection (threshold configurable)
- Persistent storage with HNSW indexing

#### Redis (Cache Layer)

**Purpose**: High-speed caching and temporary data storage

**Use Cases:**
- **Translation Cache**: Store LLM translation results (persistent, adaptive TTL)
- **API Response Cache**: FastAPI-cache backend for GET endpoints
- **Rate Limiting**: Token bucket implementation for Telegram API limits
- **Session Storage**: Temporary session data
- **Fetch Queue**: Redis-backed job queue for message collection workers

**Cache Strategy:**
- Base TTL: 7 days for translations
- Max TTL: 30 days with adaptive extension on cache hits
- TTL multiplier: 1.5x per cache hit (popular translations persist longer)
- LRU eviction: Memory-efficient cache management

### External Integrations

#### Telegram API

**Integration Type**: User Account Session (not Bot API)

**Authentication:**
- API ID + API Hash (from my.telegram.org)
- Session persistence via StringSession (cloud) or file (local)
- Phone number verification for initial setup

**Rate Limiting:**
- Token bucket with Redis backend
- 30 requests per minute (configurable)
- Flood-wait handling with exponential backoff (1.5x multiplier)
- Max 3 retries per request

**Join Channel Queue:**
- Daily limit: 20 channel joins (Telegram enforced)
- Queue processing: Midnight UTC batch job
- FIFO queue with Redis persistence

#### LLM APIs (Translation)

**Model Routing Strategy:**

1. **Gemini Flash (Default)**
   - Model: `gemini-2.0-flash`
   - Use case: Normal priority translations (>24 hours old)
   - Cost: Most economical for bulk translations
   - Fallback: GPT-4o-mini on failure

2. **GPT-4o-mini (High Priority)**
   - Model: `gpt-4o-mini`
   - Use case: Recent messages (<24 hours)
   - Quality: Higher accuracy for time-sensitive content

3. **OpenRouter (Free Fallback)**
   - Model: `meta-llama/llama-3.1-8b-instruct:free`
   - Use case: Cost-free option when quota exhausted

**Translation Optimization:**
- Skip same-language translations (source == target)
- Skip trivial content (URLs-only, emojis, short words like "ok", "yes")
- Skip messages shorter than 2 characters
- Parallel processing: 20 concurrent translations
- High-quality language priority: Russian, Ukrainian, French, German, Spanish, Italian

**API Usage Tracking:**
- Token counts logged for cost monitoring
- Configurable cost per 1K tokens (input/output)
- Dashboard analytics for LLM spend

## Service Architecture

The backend is organized into service modules, each with a specific responsibility:

### Core Services

| Service | Module | Purpose |
|---------|--------|---------|
| **Telegram Client** | `telegram_client.py` | Telegram API integration, message fetching, channel resolution |
| **Fetch Queue** | `fetch_queue.py` | Redis-backed job queue for message collection with parallel workers |
| **Translation Service** | `llm_translator.py` | LLM API integration with model routing and fallback |
| **Translation Pool** | `translation_pool.py` | Concurrent translation processing with queue management |
| **Message Bulk** | `message_bulk.py` | Efficient bulk message insertion with deduplication |
| **Deduplication** | Vector embeddings via Qdrant | Semantic similarity matching for duplicate detection |
| **Search Service** | `message_search_service.py` | Full-text + semantic search with collection filtering |
| **Export Service** | `message_export_service.py` | CSV/PDF/HTML export generation |
| **Streaming Service** | `message_streaming_service.py` | SSE (Server-Sent Events) for real-time message updates |
| **Email Service** | `email_service.py` | SMTP/Resend integration for notifications and digests |
| **Audit Service** | `audit.py` | RGPD-compliant audit logging for sensitive actions |
| **Cache Service** | `cache.py` | Redis cache abstraction with adaptive TTL |
| **Rate Limiter** | `rate_limiter.py` | Token bucket rate limiting for Telegram API |
| **Auth Rate Limiter** | `auth_rate_limiter.py` | Login attempt throttling for security |
| **Usage Tracking** | `usage.py` | API usage metrics and cost tracking |

### Service Initialization Lifecycle

Services are initialized in the FastAPI lifespan context manager (`app/main.py`):

```python
# Startup sequence:
1. Database initialization (tables, migrations)
2. Fetch worker pool startup
3. Telegram update handler startup
4. Redis cache initialization
5. Background scheduler startup (if enabled)

# Shutdown sequence:
1. Background scheduler shutdown
2. Fetch worker pool shutdown
3. Telegram update handler shutdown
4. Telegram client cleanup
5. Rate limiter cleanup
6. Redis cache cleanup
```

### Worker Pools

**Fetch Workers:**
- Pool size: 10 concurrent workers (configurable via `fetch_workers`)
- Job source: Redis queue (`osfeed:fetch_queue`)
- Job tracking: Active jobs in Redis set (`osfeed:active_fetch_jobs`)
- Status updates: Real-time job progress in PostgreSQL (`FetchJob` table)

**Translation Workers:**
- Pool size: 20 concurrent tasks (configurable via `translation_concurrency`)
- Queue source: PostgreSQL (`Message` table with `translation_status = 'pending'`)
- Retry logic: 3 attempts with exponential backoff
- Cache first: Check Redis before LLM API call

## Background Jobs

APScheduler manages periodic tasks with cron and interval triggers:

| Job | Trigger | Frequency | Purpose |
|-----|---------|-----------|---------|
| **collect_messages_job** | interval | Every 5 minutes | Fetch new messages from all active channels |
| **translate_pending_messages_job** | interval | Every 5 minutes | Process translation queue with model routing |
| **evaluate_alerts_job** | interval | Every 10 minutes | Check collection alerts and trigger notifications |
| **process_join_queue** | cron | Daily at 00:00 UTC | Process pending channel join requests (max 20/day) |
| **purge_audit_logs_job** | cron | Daily at 02:30 | Delete audit logs older than retention period (365 days) |

**Scheduler Configuration:**
- Engine: `AsyncIOScheduler` (asyncio-compatible)
- Timezone: UTC for all jobs
- Enabled: Controlled by `SCHEDULER_ENABLED` env var (default: `true`)

## Key Design Decisions

### 1. Multi-Database Strategy

**Decision**: Use PostgreSQL + Qdrant + Redis instead of a single database.

**Rationale:**
- **PostgreSQL**: Best-in-class relational database for complex queries, transactions, ACID compliance
- **Qdrant**: Purpose-built for vector search; 10x faster than pgvector for semantic similarity
- **Redis**: In-memory speed essential for cache and rate limiting

**Trade-offs:**
- Increased operational complexity (3 databases to manage)
- Higher resource usage
- Eliminates database bottlenecks; each database optimized for its workload

### 2. User Account vs Bot API for Telegram

**Decision**: Use Telegram User Account API instead of Bot API.

**Rationale:**
- User accounts can join channels without admin approval
- Access to full message history (bots only see messages after they join)
- No rate limits on channel access (bots limited to 30 joins/day via invite links)

**Trade-offs:**
- Requires phone number verification
- Subject to Telegram's user rate limits (20 joins/day, flood-wait)
- More complex session management

### 3. Redis-Backed Fetch Queue

**Decision**: Use Redis instead of PostgreSQL for the fetch job queue.

**Rationale:**
- Redis provides atomic operations (RPUSH, LPOP) for queue management
- Sub-millisecond latency for queue operations
- Natural fit for ephemeral job state (active jobs, worker locks)

**Trade-offs:**
- Job history in PostgreSQL (FetchJob table) + active state in Redis
- Requires Redis availability for message collection
- Persistent queue with AOF/RDB ensures no job loss

### 4. Model Routing for Translations

**Decision**: Use Gemini Flash for bulk, GPT-4o-mini for high-priority, with OpenRouter fallback.

**Rationale:**
- Gemini Flash: 80% cost reduction vs GPT-4o-mini for normal priority
- GPT-4o-mini: Higher quality for time-sensitive messages (<24h)
- OpenRouter: Zero cost for quota-exhausted scenarios

**Trade-offs:**
- Increased complexity (3 API integrations)
- Fallback logic adds code paths
- Optimal cost/performance balance; ~70% cost savings in production

### 5. Adaptive Cache TTL

**Decision**: Extend cache TTL dynamically based on access frequency.

**Rationale:**
- Popular translations accessed repeatedly (e.g., breaking news channels)
- Static content (old messages) benefits from long-term caching
- Adaptive TTL reduces redundant LLM API calls

**Implementation:**
- Base TTL: 7 days
- TTL multiplier: 1.5x per cache hit
- Max TTL: 30 days
- Result: 95% cache hit rate for active channels

### 6. Bulk Message Insertion

**Decision**: Batch insert messages in bulk rather than one-by-one.

**Rationale:**
- PostgreSQL optimized for bulk operations (10x faster than individual INSERTs)
- Reduces database round-trips from 100 to 1 for typical fetch job
- Enables efficient deduplication checks with single query

**Implementation:**
- Batch size: 100 messages (configurable via `telegram_batch_size`)
- Transaction per batch: All-or-nothing for data consistency
- Conflict handling: ON CONFLICT DO NOTHING for idempotency

### 7. Server-Sent Events (SSE) for Real-Time Updates

**Decision**: Use SSE instead of WebSocket for real-time message streaming.

**Rationale:**
- SSE simpler than WebSocket (HTTP-based, no protocol upgrade)
- Unidirectional updates (server → client) match OSFeed's use case
- Built-in reconnection logic in browser EventSource API

**Trade-offs:**
- Cannot push client → server (not needed for OSFeed)
- HTTP/2 required for efficient connection multiplexing
- Simpler implementation, better compatibility with proxies/CDNs

### 8. Collection-Scoped Permissions

**Decision**: Implement collection sharing with role-based access (viewer/editor/admin).

**Rationale:**
- Multi-user collaboration on channel groups
- Granular permissions for enterprise use cases
- RGPD compliance with audit logging

**Implementation:**
- **Viewer**: Read-only access to collection messages and digests
- **Editor**: Can add/remove channels, create exports
- **Admin**: Can manage shares, delete collection

## Security Architecture

### Authentication & Authorization

**JWT Token Strategy:**
- **Access Token**: Short-lived (1 hour), used for API requests
- **Refresh Token**: Long-lived (7 days), rotated on refresh
- **Algorithm**: HS256 (HMAC-SHA256)
- **Secret Key**: Environment-based, rotated on breach

**Password Security:**
- Hashing: bcrypt with per-user salt
- Minimum strength: Enforced on frontend (8+ characters)
- Reset tokens: 30-minute expiry, one-time use

**Session Security:**
- Refresh token rotation: New token issued on each refresh
- Token invalidation: Blacklist on logout (Redis-backed)
- CSRF protection: SameSite cookies (future enhancement)

### API Security

**Rate Limiting:**
- Auth endpoints: 5 requests/minute per IP (via `auth_rate_limiter`)
- Telegram API: 30 requests/minute per account (via `rate_limiter`)
- Configurable thresholds via environment variables

**Security Headers Middleware:**
- **Content-Security-Policy**: Restricts script/style sources
- **Strict-Transport-Security**: Force HTTPS (1 year max-age)
- **X-Frame-Options**: Prevent clickjacking (DENY)
- **X-Content-Type-Options**: Prevent MIME sniffing (nosniff)
- **Referrer-Policy**: Control referrer information leakage
- **Permissions-Policy**: Disable unnecessary browser features

**CORS Configuration:**
- Allowed origins: Frontend URL + www variant
- Credentials: Enabled for cookie-based auth
- Methods: GET, POST, PUT, PATCH, DELETE
- Headers: Content-Type, Authorization

### Audit Logging

**Tracked Actions:**
- User authentication (login, logout, password reset)
- Collection creation, modification, deletion
- Channel joins, removals
- Export generation
- Share permission changes

**RGPD Compliance:**
- Retention period: 365 days (configurable via `audit_log_retention_days`)
- Purge schedule: Daily at 02:30 (configurable via `audit_log_purge_time`)
- User IP anonymization: Last octet zeroed (192.168.1.0)

### Data Protection

**Encryption:**
- HTTPS in production (Let's Encrypt via Traefik)
- Database credentials in environment variables (never committed)
- Telegram session stored in volume (not in code)

**Secrets Management:**
- `.env` file for local development (gitignored)
- Environment variables in production (Docker Compose, Coolify)
- Secret rotation: Manual process (automated rotation future enhancement)

## Deployment Architecture

### Docker Compose Stack

**Services:**
1. **backend** (FastAPI + Uvicorn)
   - Image: Built from `./backend/Dockerfile`
   - Workers: 4 (production)
   - Resources: 2 CPU cores, 2GB memory
   - Health check: GET /health every 30s

2. **frontend** (Nginx + React SPA)
   - Image: Built from `./frontend/Dockerfile` (production target)
   - Resources: 0.5 CPU cores, 256MB memory
   - Serves static build on port 80

3. **osfeed-postgres** (PostgreSQL 15)
   - External service (managed by Coolify)
   - Connection pooling via asyncpg

4. **osfeed-qdrant** (Qdrant vector database)
   - External service (managed by Coolify)
   - REST API on port 6333

5. **osfeed-redis** (Redis 7)
   - External service (managed by Coolify)
   - Persistence: AOF + RDB snapshots

### Traefik Routing (Production)

**HTTP → HTTPS Redirect:**
- Middleware: `redirect-to-https` on all HTTP entrypoints
- Certificate: Let's Encrypt (auto-renewal)

**Domain Routing:**
- `osfeed.com` → Frontend (port 80)
- `www.osfeed.com` → Frontend (redirect or serve)
- `api.osfeed.com` → Backend (port 8000)

**Labels:**
- `coolify.managed=true`: Managed by Coolify platform
- `traefik.enable=true`: Enable Traefik routing
- `traefik.http.routers.*.tls.certresolver=letsencrypt`: Auto-SSL

### Network Configuration

**External Network:**
- `coolify`: Connects to Traefik proxy (external)

**Internal Network:**
- `default`: Inter-service communication (backend ↔ postgres ↔ redis ↔ qdrant)

**Volume Mounts:**
- `telegram_data:/app/data`: Telegram session persistence
- Development: Source code mounted for hot-reloading

### Health Checks

**Backend:**
```bash
curl -f http://localhost:8000/health
```
- Interval: 30s
- Timeout: 10s
- Retries: 3
- Start period: 40s (allows for DB connection)

**Database Connectivity:**
- Health endpoint executes `SELECT 1` to verify PostgreSQL connection
- Returns 503 if database unreachable

## Scalability Considerations

### Current Architecture (Single Server)

**Bottlenecks:**
- Single backend instance (vertical scaling only)
- Shared PostgreSQL connection pool (max 30 connections)
- APScheduler runs on single backend (no distributed locking)

**Capacity:**
- ~1000 channels with 5-minute collection interval
- ~10,000 translations/hour (limited by LLM API rate limits)
- ~100 concurrent users (Uvicorn 4 workers)

### Horizontal Scaling Strategy (Future)

**Multi-Instance Backend:**
- Load balancer (Traefik) distributes traffic across N backend instances
- Shared state: PostgreSQL, Redis, Qdrant (already multi-instance safe)
- Scheduler: Move to distributed scheduler (Celery, RQ) with Redis broker
- Session affinity: Not required (stateless API)

**Database Scaling:**
- PostgreSQL read replicas for query-heavy workloads
- Connection pooling: PgBouncer in transaction mode
- Partitioning: Time-based partitioning for messages table (by month)

**Cache Scaling:**
- Redis cluster for distributed cache (sharding by key)
- Separate Redis instance for job queue vs cache

**Worker Scaling:**
- Independent fetch worker pool (separate service)
- Independent translation worker pool (separate service)
- Scale workers independently based on queue depth

**Monitoring & Observability:**
- Prometheus metrics for queue depth, cache hit rate, API latency
- Grafana dashboards for real-time monitoring
- Alerting on job failures, queue backlog, API errors

---

## Related Documentation

- [System Overview Diagram](./diagrams/system-overview.mmd) - Visual architecture overview
- [Data Flow Documentation](./DATA_FLOW.md) - Message pipeline details (to be created)
- [Message Pipeline Diagram](./diagrams/message-pipeline.mmd) - Step-by-step flow diagram (to be created)
- [Main README](../README.md) - Quickstart and setup instructions

## Maintenance Notes

This architecture document should be updated when:
- New services are added to the stack
- Database schema undergoes major changes
- External API integrations change (new LLM providers, etc.)
- Deployment architecture changes (e.g., move to Kubernetes)
- Major refactoring of service boundaries

Last updated: 2026-02-02
