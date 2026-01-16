# TeleScope

TeleScope is a Telegram-first OSINT platform for collection, translation, deduplication, and daily digests.

## Highlights

- Telegram collection with flood-wait handling
- LLM translation (OpenAI GPT-4o-mini) with fallback
- Vector deduplication (Pinecone) + semantic search hooks
- Daily digests v2 (HTML + PDF export + key entities)
- Collections to group channels and filter digests
- KPI dashboard (messages, channels, duplicates) with CSV export
- Audit logs for sensitive actions (RGPD)

## Quickstart (local)

1) Start everything
```
./start.sh
```

2) Open the app
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Environment

The first run copies `.env.example` to `.env` if missing. Update `.env` with:
- PostgreSQL credentials
- OpenAI / Pinecone keys
- Telegram API credentials

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

## Requirements

- Python 3.11-3.13
- Node.js
- Docker + Docker Compose (for PostgreSQL)
