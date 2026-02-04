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

## Environment Variables Reference

The first run copies `.env.example` to `.env` if missing. All environment variables are read from `.env` with case-insensitive matching.

### Authentication

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | **Yes** | - | Application secret key for JWT tokens and session signing. Generate with: `openssl rand -hex 32` |
| `ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Access token lifetime (1 hour) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token lifetime (7 days) |
| `COOKIE_ACCESS_TOKEN_NAME` | No | `access_token` | Name of the access token cookie |
| `COOKIE_REFRESH_TOKEN_NAME` | No | `refresh_token` | Name of the refresh token cookie |
| `COOKIE_SECURE` | No | `false` | **Set to `true` in production with HTTPS** to prevent cookie transmission over insecure connections |
| `COOKIE_SAMESITE` | No | `lax` | CSRF protection; options: `lax`, `strict`, or `none` |
| `COOKIE_DOMAIN` | No | - | Specific domain for cookies; leave empty for default behavior |

### Database (PostgreSQL)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_HOST` | No | `localhost` | PostgreSQL server hostname |
| `POSTGRES_PORT` | No | `5432` | PostgreSQL server port |
| `POSTGRES_DB` | No | `osfeed_db` | Database name |
| `POSTGRES_USER` | No | `osfeed_user` | Database username |
| `POSTGRES_PASSWORD` | **Yes** | - | Database password |
| `USE_SQLITE` | No | `false` | Set to `true` for local dev without PostgreSQL |
| `SQLITE_URL` | No | `sqlite+aiosqlite:///./data/osfeed.db` | SQLite database path (fallback) |
| `DB_POOL_SIZE` | No | `20` | PostgreSQL connection pool size |
| `DB_MAX_OVERFLOW` | No | `10` | Max overflow connections beyond pool size |
| `DB_POOL_RECYCLE` | No | `1800` | Seconds before connection recycling (30 minutes) |

### API Server

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_HOST` | No | `0.0.0.0` | Backend API bind address |
| `API_PORT` | No | `8000` | Backend API port |
| `FRONTEND_URL` | No | `http://localhost:5173` | Frontend URL for CORS configuration |

### OpenAI API

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Recommended | - | OpenAI API key for translations and embeddings |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model for translations |

### Gemini API

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Recommended | - | Google Gemini API key for cost-effective translations |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Gemini model for translations |

### OpenRouter API

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | No | - | OpenRouter API key (optional fallback for free LLM access) |
| `OPENROUTER_MODEL` | No | `meta-llama/llama-3.1-8b-instruct:free` | OpenRouter model selection |

### Telegram API

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_API_ID` | **Yes** | `0` | Telegram API ID from https://my.telegram.org |
| `TELEGRAM_API_HASH` | **Yes** | - | Telegram API hash from https://my.telegram.org |
| `TELEGRAM_PHONE` | **Yes** | - | Phone number with country code (e.g., `+33612345678`) |
| `TELEGRAM_SESSION_PATH` | No | `/app/data/telegram.session` | File path for Telegram session storage |
| `TELEGRAM_SESSION_STRING` | Recommended | - | StringSession for cloud deployments (takes priority over file) |
| `TELEGRAM_REQUESTS_PER_MINUTE` | No | `30` | Rate limit for Telegram API requests |
| `TELEGRAM_FLOOD_WAIT_MULTIPLIER` | No | `1.5` | Multiplier for flood wait backoff |
| `TELEGRAM_MAX_RETRIES` | No | `3` | Max retry attempts for failed requests |
| `TELEGRAM_JOIN_CHANNEL_DAILY_LIMIT` | No | `20` | Daily limit for joining channels (Telegram enforces ~20/day) |
| `TELEGRAM_JOIN_CHANNEL_QUEUE_ENABLED` | No | `true` | Enable queue for channel join requests |
| `TELEGRAM_FETCH_WORKERS` | No | `3` | Number of parallel fetch workers |
| `TELEGRAM_BATCH_SIZE` | No | `100` | Batch size for message fetching |
| `TELEGRAM_SYNC_INTERVAL_SECONDS` | No | `300` | Sync interval in seconds (5 minutes) |

### Redis Cache

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | Recommended | - | Redis connection URL (e.g., `redis://redis:6379/0`) |
| `REDIS_CACHE_TTL_SECONDS` | No | `86400` | Default cache TTL (24 hours) |
| `ENABLE_RESPONSE_CACHE` | No | `true` | Enable response caching |
| `RESPONSE_CACHE_TTL` | No | `30` | Response cache TTL in seconds |

### Email Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EMAIL_ENABLED` | No | `false` | Enable email functionality (app works without email) |
| `EMAIL_PROVIDER` | No | `smtp` | Email provider: `smtp` or `resend` |
| `EMAIL_FROM_ADDRESS` | No | `noreply@osfeed.app` | Sender email address |
| `EMAIL_FROM_NAME` | No | `OSFeed` | Sender display name |
| `SMTP_HOST` | No | - | SMTP server hostname (required if EMAIL_PROVIDER=smtp) |
| `SMTP_PORT` | No | `587` | SMTP server port |
| `SMTP_USER` | No | - | SMTP username |
| `SMTP_PASSWORD` | No | - | SMTP password |
| `SMTP_USE_TLS` | No | `true` | Use TLS for SMTP connection |
| `RESEND_API_KEY` | No | - | Resend API key (required if EMAIL_PROVIDER=resend) |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | No | `30` | Password reset token lifetime |
| `EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS` | No | `24` | Email verification token lifetime |

### Security Headers

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECURITY_HEADERS_ENABLED` | No | `true` | Enable security headers middleware |
| `SECURITY_CSP_ENABLED` | No | `true` | Enable Content-Security-Policy header |
| `SECURITY_CSP_DIRECTIVES` | No | See config.py | Content-Security-Policy directives |
| `SECURITY_HSTS_ENABLED` | No | `true` | Enable Strict-Transport-Security header |
| `SECURITY_HSTS_MAX_AGE` | No | `31536000` | HSTS max-age in seconds (1 year) |
| `SECURITY_HSTS_INCLUDE_SUBDOMAINS` | No | `true` | Include subdomains in HSTS |
| `SECURITY_X_FRAME_OPTIONS` | No | `DENY` | X-Frame-Options value: `DENY` or `SAMEORIGIN` |
| `SECURITY_X_CONTENT_TYPE_OPTIONS` | No | `true` | Enable X-Content-Type-Options: nosniff |
| `SECURITY_REFERRER_POLICY` | No | `strict-origin-when-cross-origin` | Referrer-Policy header value |
| `SECURITY_PERMISSIONS_POLICY` | No | See config.py | Permissions-Policy header (restricts browser features) |

### Translation Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TRANSLATION_CONCURRENCY` | No | `20` | Number of concurrent translation requests |
| `TRANSLATION_DEFAULT_MODEL` | No | `gemini-flash` | Default model: `gemini-flash`, `gpt-4o-mini`, or `google` |
| `TRANSLATION_HIGH_PRIORITY_MODEL` | No | `gpt-4o-mini` | Model for high-priority messages (<24h old) |
| `TRANSLATION_SKIP_SAME_LANGUAGE` | No | `true` | Skip translation if source == target language |
| `TRANSLATION_SKIP_TRIVIAL` | No | `true` | Skip URLs-only, emojis-only, etc. |
| `TRANSLATION_SKIP_SHORT_WORDS` | No | See config.py | List of short words to skip (ok, yes, no, etc.) |
| `TRANSLATION_SKIP_SHORT_MAX_CHARS` | No | `2` | Max characters for short-word skipping |
| `TRANSLATION_HIGH_PRIORITY_HOURS` | No | `24` | Messages younger than this are high-priority |
| `TRANSLATION_NORMAL_PRIORITY_DAYS` | No | `7` | Messages 1-7 days old are normal priority |
| `TRANSLATION_HIGH_QUALITY_LANGUAGES` | No | See config.py | Languages requiring higher quality models |
| `TRANSLATION_CACHE_BASE_TTL` | No | `604800` | Base cache TTL (7 days) |
| `TRANSLATION_CACHE_MAX_TTL` | No | `2592000` | Max cache TTL (30 days) |
| `TRANSLATION_CACHE_HIT_MULTIPLIER` | No | `1.5` | TTL multiplier per cache hit |
| `TRANSLATION_MEMORY_CACHE_MAX_SIZE` | No | `1000` | Max entries in LRU translation memory cache |

### Application Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PREFERRED_LANGUAGE` | No | `en` | Default application language |
| `SUMMARY_TIME` | No | `08:00` | Daily digest generation time (HH:MM format) |
| `APP_DEBUG` | No | `false` | Enable debug mode (verbose logging) |
| `SCHEDULER_ENABLED` | No | `true` | Enable background scheduler (digests, cleanup) |
| `FETCH_WORKERS` | No | `10` | Number of parallel message fetch workers |

### Audit Logs

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AUDIT_LOG_RETENTION_DAYS` | No | `365` | Days to retain audit logs (GDPR compliance) |
| `AUDIT_LOG_PURGE_TIME` | No | `02:30` | Daily purge time for old audit logs (HH:MM format) |

### API Usage Tracking

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_USAGE_TRACKING_ENABLED` | No | `true` | Enable API usage tracking for LLM cost monitoring |
| `LLM_COST_INPUT_PER_1K` | No | `0.0` | Cost per 1K input tokens (for cost tracking) |
| `LLM_COST_OUTPUT_PER_1K` | No | `0.0` | Cost per 1K output tokens (for cost tracking) |

### Quick Setup Checklist

**Minimum required variables for first run:**
1. `SECRET_KEY` - Generate with `openssl rand -hex 32`
2. `POSTGRES_PASSWORD` - Set a secure password
3. At least one LLM provider (`OPENAI_API_KEY` or `GEMINI_API_KEY`)
4. Telegram credentials (`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`, `TELEGRAM_SESSION_STRING`)

**Production hardening:**
- Set `COOKIE_SECURE=true` (requires HTTPS)
- Configure `REDIS_URL` for persistent translation caching
- Set `EMAIL_ENABLED=true` and configure SMTP/Resend
- Enable security headers (enabled by default)
- Set appropriate `SECURITY_CSP_DIRECTIVES` for your domain

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

- **Cookie-based Authentication:**
  - Authentication tokens are stored in secure httpOnly cookies (not accessible to JavaScript)
  - `POST /api/auth/login` sets `access_token` and `refresh_token` as httpOnly cookies, returns user info
  - `POST /api/auth/refresh` reads refresh token from cookies, rotates it, and sets new cookies
  - `POST /api/auth/logout` clears both authentication cookies
  - All authenticated requests automatically include cookies (use `credentials: 'include'` in fetch/axios)
  - **Security benefits:** XSS attacks cannot steal tokens; CSRF protection via SameSite attribute
- API usage stats:
  - `GET /api/stats/api-usage?days=7`

## Documentation

For detailed technical documentation:
- [Architecture Overview](docs/ARCHITECTURE.md) - System components, deployment, and infrastructure
- [Data Flow Guide](docs/DATA_FLOW.md) - Message processing pipeline and data flows

## Troubleshooting

### Telegram Session Setup

If you encounter "Unauthorized" errors when fetching Telegram messages, you need to set up a valid Telegram session.

**Interactive Setup:**
```bash
docker compose exec backend python -m app.cli.telegram_setup
```

This tool will:
1. Prompt for API credentials (or read from environment)
2. Send authentication code via Telegram
3. Prompt for SMS/Telegram code
4. Handle 2FA password if enabled
5. Generate a `TELEGRAM_SESSION_STRING` for your `.env`

**Required Environment Variables:**
- `TELEGRAM_API_ID` - Get from https://my.telegram.org
- `TELEGRAM_API_HASH` - Get from https://my.telegram.org
- `TELEGRAM_PHONE` - Phone number with country code (e.g., `+33612345678`)
- `TELEGRAM_SESSION_STRING` - Generated by the setup tool

**Common Issues:**
- **FloodWaitError**: Telegram rate limit reached. Wait the specified time before retrying.
- **SessionPasswordNeededError**: 2FA is enabled. Set `TELEGRAM_2FA_PASSWORD` in `.env` or enter when prompted.
- **Invalid session**: Delete old session files and re-run the setup tool.

### LLM API Key Configuration

OSFeed requires at least one LLM provider for translations. Configure your preferred provider(s):

**OpenAI (Recommended for quality):**
```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

**Gemini (Recommended for cost):**
```env
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.0-flash
TRANSLATION_DEFAULT_MODEL=gemini-flash
```

**OpenRouter (Fallback/Free tier):**
```env
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

**Testing API Keys:**
```bash
# Check backend logs for translation errors
docker compose logs -f backend | grep -i "translation\|llm\|api"
```

**Common Issues:**
- **401 Unauthorized**: Invalid API key. Check for extra spaces or incorrect key format.
- **429 Rate Limit**: You've exceeded the provider's rate limit. Wait or upgrade your plan.
- **503 Service Unavailable**: Provider is down. Configure a fallback provider.
- **No translations**: Ensure at least one of `OPENAI_API_KEY` or `GEMINI_API_KEY` is set.

### Qdrant Connection Issues

Qdrant is used for vector embeddings and deduplication.

**Check Qdrant Status:**
```bash
docker compose ps qdrant
docker compose logs qdrant
```

**Test Connection:**
```bash
curl http://localhost:6333/collections
```

**Environment Variables:**
```env
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=  # Optional for local development
```

**Common Issues:**
- **Connection refused**: Qdrant container not running. Run `docker compose up -d qdrant`.
- **Collection not found**: Collections are created automatically on first use.
- **Out of memory**: Increase Docker memory limit (Settings → Resources → Memory).

### Database Migration Errors

If you encounter database schema errors, you may need to run migrations manually.

**Check Migration Status:**
```bash
docker compose exec backend alembic current
docker compose exec backend alembic history
```

**Apply Pending Migrations:**
```bash
docker compose exec backend alembic upgrade head
```

**Rollback Last Migration:**
```bash
docker compose exec backend alembic downgrade -1
```

**Create New Migration:**
```bash
docker compose exec backend alembic revision --autogenerate -m "description"
```

**Common Issues:**
- **"Target database is not up to date"**: Run `alembic upgrade head`.
- **"Can't locate revision identified by 'xyz'"**: Database and migration files are out of sync. Check `alembic_version` table.
- **Connection refused**: PostgreSQL container not ready. Wait 10-15 seconds after `docker compose up`.
- **SQLite to PostgreSQL migration**: Run `MIGRATE_SQLITE=1 ./start.sh` if you have existing SQLite data.

### Redis Connection Issues

Redis is optional but recommended for translation caching.

**Check Redis Status:**
```bash
docker compose ps redis
docker compose logs redis
```

**Test Connection:**
```bash
docker compose exec redis redis-cli ping
# Should return: PONG
```

**Environment Variables:**
```env
REDIS_URL=redis://redis:6379/0
REDIS_CACHE_TTL_SECONDS=86400
ENABLE_RESPONSE_CACHE=true
```

**Common Issues:**
- **Connection refused**: Redis container not running. Run `docker compose up -d redis`.
- **NOAUTH Authentication required**: Set `REDIS_PASSWORD` in `.env` if Redis has authentication enabled.
- **Out of memory**: Redis evicts old cache entries automatically (LRU policy).
- **App works without Redis**: Translation cache will be disabled but app continues to function.

### Docker Compose Startup Failures

**View All Service Status:**
```bash
docker compose ps
docker compose logs
```

**Restart Specific Service:**
```bash
docker compose restart backend
docker compose restart frontend
```

**Rebuild After Code Changes:**
```bash
docker compose down
docker compose build --no-cache backend
docker compose up -d
```

**Common Issues:**
- **Port already in use**: Another service is using ports 5173, 8000, 5432, 6333, or 6379. Stop conflicting services or change ports in `docker-compose.yml`.
- **Volume mount errors**: Ensure Docker has permission to access the project directory (Docker Desktop → Settings → Resources → File Sharing).
- **Backend fails to start**: Check `.env` file exists and `SECRET_KEY` is set. Run `./start.sh` to auto-generate.
- **Frontend build errors**: Delete `frontend/node_modules` and `frontend/.vite` cache, then rebuild.
- **Database connection timeout**: PostgreSQL takes 10-15 seconds to initialize on first run. Wait and retry.
- **"exec format error"**: Architecture mismatch. Rebuild images with `docker compose build --no-cache`.

**Complete Reset (Nuclear Option):**
```bash
docker compose down -v  # Removes volumes (deletes data!)
docker system prune -a  # Cleans all Docker resources
./start.sh              # Fresh start
```

## Requirements

- Docker + Docker Compose (PostgreSQL, Qdrant, Redis, Backend, Frontend)
- No local Python/Node dependencies required!
