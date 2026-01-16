# TeleScope

TeleScope is a Telegram-first OSINT platform for collection, translation, deduplication, and daily digests.

## Highlights

- Telegram collection with flood-wait handling
- LLM translation (OpenAI GPT-4o-mini) with fallback
- Vector deduplication (Qdrant) + semantic search hooks
- Daily digests v2 (HTML + PDF export + key entities)
- Collections to group channels and filter digests
- KPI dashboard (messages, channels, duplicates) with CSV export
- Frontend refonte (React 18 + Vite + Tailwind + Zustand + React Query)
- Command palette (⌘K) + global shortcuts
- Virtualized message feed + lazy-loaded routes
- PWA (offline install ready)
- Redis cache for translations (persistent)
- Audit logs for sensitive actions (RGPD)
- Refresh tokens + session rotation
- API usage tracking (LLM cost monitoring)

## Quickstart (local)

1) Start everything
```
./start.sh
```

2) Open the app
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Frontend dev

```
cd frontend
npm install
npm run dev
```

Run E2E tests:
```
cd frontend
npm run test:e2e
```

## Environment

The first run copies `.env.example` to `.env` if missing. Update `.env` with:
- PostgreSQL credentials
- OpenAI / Qdrant settings
- Telegram API credentials
- Redis settings (optional but recommended for translation cache)
- Optional settings:
  - `SCHEDULER_ENABLED` (default `true`)
  - `AUDIT_LOG_RETENTION_DAYS` (default `365`)
  - `AUDIT_LOG_PURGE_TIME` (default `02:30`)
  - `API_USAGE_TRACKING_ENABLED` (default `true`)
  - `LLM_COST_INPUT_PER_1K` (default `0.0`)
  - `LLM_COST_OUTPUT_PER_1K` (default `0.0`)

## PostgreSQL setup

The default flow uses PostgreSQL via Docker Compose. The `start.sh` script:
- starts PostgreSQL (unless `USE_SQLITE=true` or `SKIP_POSTGRES=1`)
- runs Alembic migrations
- optionally migrates SQLite data to PostgreSQL

### Optional migration

If you have an existing SQLite database in `data/telescope.db`, run:
```
MIGRATE_SQLITE=1 ./start.sh
```

This will run:
- `backend/scripts/migrate_sqlite_to_postgres.py`
- after Alembic migrations

### Manual migration (alternative)
```
docker compose up -d
cd backend
alembic upgrade head
python3 scripts/migrate_sqlite_to_postgres.py --dry-run
python3 scripts/migrate_sqlite_to_postgres.py
python3 scripts/check_postgres.py
```

## API notes

- Auth refresh flow:
  - `POST /api/auth/login` returns `access_token` + `refresh_token`
  - `POST /api/auth/refresh` rotates refresh token and returns a new access token
- API usage stats:
  - `GET /api/stats/api-usage?days=7`

## Requirements

- Python 3.11-3.13 (3.14 not supported by Pydantic yet)
- Node.js
- Docker + Docker Compose (PostgreSQL, Qdrant, Redis)
