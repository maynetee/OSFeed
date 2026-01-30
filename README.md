# OSFeed

OSFeed is a Telegram-first OSINT platform for collection, translation, deduplication, and daily digests.

## Highlights

- Telegram collection with flood-wait handling
- LLM translation with model routing (Gemini Flash default, GPT-4o-mini for high-priority) + fallback
- Vector deduplication (Qdrant) + semantic search hooks
- Daily digests v2 (HTML + PDF export + key entities)
- Collections to group channels, filter digests, and export scoped messages
- Collection stats + dashboard scope selector
- Collection alerts + in-app notifications
- Collection sharing (viewer/editor/admin)
- KPI dashboard (messages, channels, duplicates) with CSV export
- Frontend refonte (React 18 + Vite + Tailwind + Zustand + React Query)
- Command palette (⌘K) + global shortcuts
- Virtualized message feed + lazy-loaded routes
- Full-text + semantic search with similar-message view
- Message exports CSV/PDF/HTML + digests history pagination
- Collection-aware search filters
- Trust indicators (duplicate score, primary source)
- i18n FR/EN
- PWA (offline install ready)
- Redis cache for translations (persistent)
- Audit logs for sensitive actions (RGPD)
- Refresh tokens + session rotation
- API usage tracking (LLM cost monitoring)

## Quickstart (Full Docker)

OSFeed runs entirely in Docker for both development and production. Hot-reloading is enabled via volume mounts.

1) Start everything
```bash
./start.sh
```
*This command starts Docker services, waits for readiness, and applies database migrations.*

2) Open the app
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

3) Stop the app
```bash
./stop.sh
```

## Logs & Debugging

View logs for all services:
```bash
docker compose logs -f
```

View specific logs:
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

## Environment

The first run copies `.env.example` to `.env` if missing. Update `.env` with:
- **SECRET_KEY** (required) - Application secret key for JWT tokens and session signing
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

The `start.sh` script automatically handles PostgreSQL startup and migrations.

### Optional migration

If you have an existing SQLite database in `data/osfeed.db`, run:
```bash
MIGRATE_SQLITE=1 ./start.sh
```

### Manual migration (alternative)
```bash
docker compose up -d
docker compose exec backend alembic upgrade head
# Migration script if needed:
docker compose exec backend python scripts/migrate_sqlite_to_postgres.py
```

## API notes

- Auth refresh flow:
  - `POST /api/auth/login` returns `access_token` + `refresh_token`
  - `POST /api/auth/refresh` rotates refresh token and returns a new access token
- API usage stats:
  - `GET /api/stats/api-usage?days=7`

## Requirements

- Docker + Docker Compose (PostgreSQL, Qdrant, Redis, Backend, Frontend)
- No local Python/Node dependencies required!
