# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OSFeed is a Telegram-first OSINT platform for collecting, translating, deduplicating, and generating daily digests from Telegram channels. It uses a User Account API (not Bot API) for full channel access, multi-LLM translation with model routing, and vector-based semantic deduplication via Qdrant.

## Commands

### Running the App (Docker-based, no local Python/Node needed)

```bash
./start.sh              # Start all services, wait for readiness, apply migrations
./stop.sh               # Stop all services
docker compose logs -f backend   # Backend logs
docker compose logs -f frontend  # Frontend logs
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Backend Tests

```bash
# All tests (inside Docker)
docker compose exec backend pytest

# Single test file
docker compose exec backend pytest tests/test_auth_login.py

# Single test function
docker compose exec backend pytest tests/test_auth_login.py::test_login_success

# With coverage
docker compose exec backend pytest --cov=app --cov-report=html
```

CI runs tests with in-memory SQLite (`USE_SQLITE=true`, `SQLITE_URL=sqlite+aiosqlite:///:memory:`) and dummy API keys. See `.github/workflows/ci.yml` for the exact env vars.

### Backend Linting

```bash
docker compose exec backend ruff check app/ tests/
docker compose exec backend ruff check --fix app/ tests/
```

Ruff config: `backend/ruff.toml` — line length 120, Python 3.11, rules: E, F, I.

### Frontend Build & Lint

```bash
cd frontend && npm ci && npm run build   # tsc + vite build
cd frontend && npm run dev               # Vite dev server with HMR
cd frontend && npm run test:e2e          # Playwright E2E tests
```

ESLint config: `frontend/.eslintrc.json` — extends `eslint:recommended`, `@typescript-eslint/recommended`, `react-hooks/recommended`.

### Database Migrations (Alembic)

```bash
docker compose exec backend alembic upgrade head                              # Apply all
docker compose exec backend alembic downgrade -1                              # Rollback one
docker compose exec backend alembic revision --autogenerate -m "description"  # Generate new
docker compose exec backend alembic current                                   # Check status
```

Migrations auto-run on container startup via `backend/entrypoint.sh`.

## Architecture

### Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Zustand (state), React Query (server state), React Router v6 |
| Backend | FastAPI, Python 3.11, Uvicorn, SQLAlchemy 2.0 (async), Pydantic v2 |
| Primary DB | PostgreSQL (asyncpg driver) — SQLite fallback via `USE_SQLITE=true` |
| Vector DB | Qdrant (semantic dedup + search) |
| Cache | Redis (translation cache, API response cache, fetch queue, rate limiting) |
| Scheduler | APScheduler (collect messages, translate, purge audit logs, evaluate alerts, process join queue) |
| Telegram | Telethon (User Account API) |
| Auth | JWT in httpOnly cookies, refresh token rotation |
| Deployment | Docker Compose, Traefik (production), Coolify |

### Backend Structure (`backend/app/`)

```
main.py              — FastAPI app, lifespan (startup/shutdown), scheduler, middleware
config.py            — Settings from env vars (Pydantic BaseSettings)
database.py          — SQLAlchemy async engine + session factory
api/                 — Route handlers (auth, channels, messages, collections, alerts, stats, audit_logs)
models/              — SQLAlchemy models (User, Channel, Message, Collection, CollectionShare, Alert, FetchJob, AuditLog, ApiUsage)
schemas/             — Pydantic request/response models
services/            — Business logic (telegram_client, llm_translator, fetch_queue, translation_pool, cache_service, email_service, rate_limiter, etc.)
jobs/                — Background jobs (collect_messages, translate_pending_messages, purge_audit_logs, alerts)
middleware/          — Security headers middleware
```

Key pattern: API routes → services → models/database. Services encapsulate business logic; routes are thin.

### Frontend Structure (`frontend/src/`)

```
app/                 — App shell, providers, router
features/            — Feature modules (auth, channels, collections, dashboard, exports, feed, landing, search, settings)
components/          — Shared UI components (Radix UI + Tailwind)
hooks/               — Custom React hooks
stores/              — Zustand state stores
lib/                 — Utilities, API client (Axios)
locales/             — i18n translations (en, fr)
types/               — TypeScript type definitions
```

### Background Jobs (APScheduler)

| Job | Frequency | Purpose |
|-----|-----------|---------|
| collect_messages | 5 min | Fetch new messages from active channels |
| translate_pending | 5 min | Process translation queue with LLM model routing |
| evaluate_alerts | 10 min | Check collection alert conditions |
| process_join_queue | Daily 00:00 UTC | Process pending channel joins (max 20/day) |
| purge_audit_logs | Daily 02:30 | Delete old audit logs per retention policy |

### LLM Translation Routing

- **Gemini Flash** (default): Cost-effective bulk translations for messages >24h old
- **GPT-4o-mini** (high priority): Better quality for recent messages <24h old
- **OpenRouter** (fallback): Free tier when quotas exhausted
- Translations cached in Redis with adaptive TTL (7d base, 1.5x multiplier per hit, 30d max)

### Auth Flow

JWT access token (1h) + refresh token (7d) stored as httpOnly cookies. Refresh rotates both tokens. All API requests use `credentials: 'include'` for automatic cookie handling. Frontend uses Axios with interceptors for token refresh.

## Conventions

- **Commits**: Conventional commits (`feat(scope):`, `fix(scope):`, `refactor:`, `test:`, `docs:`, `chore:`)
- **Branch naming**: `feature/short-description`, `fix/issue-number-description`, `docs/what`
- **Python style**: Type hints, async/await for I/O, snake_case functions/variables, PascalCase classes
- **TypeScript style**: Functional components with hooks, TypeScript interfaces for props, camelCase variables, PascalCase components
- **Async throughout**: Both backend (asyncio/asyncpg) and frontend (React Query) are fully async
- **pytest config**: `asyncio_mode = auto` — no need for `@pytest.mark.asyncio` decorators
