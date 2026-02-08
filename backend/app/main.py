import asyncio
import uuid
import structlog
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app.api import (
    alerts,
    analysis,
    audit_logs,
    auth,
    channels,
    collections,
    contact_sales,
    digests,
    insights,
    messages,
    newsletter,
    notifications,
    stats,
    stripe,
    subscription,
    summaries,
)
from app.config import get_settings
from app.database import get_engine, init_db
from app.jobs.alerts import evaluate_alerts_job
from app.jobs.collect_messages import collect_messages_job
from app.jobs.correlate_sources import correlate_sources_job
from app.jobs.detect_patterns import detect_patterns_job
from app.jobs.purge_audit_logs import purge_audit_logs_job
from app.jobs.score_escalation import score_escalation_job
from app.jobs.score_relevance import score_relevance_job
from app.jobs.send_daily_digests import send_daily_digests_job
from app.jobs.translate_pending_messages import translate_pending_messages_job
from app.logging_config import configure_logging
from app.middleware.auth import AuthMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.seeds.curated_collections import seed_curated_collections
from app.services.channel_join_queue import process_join_queue
from app.services.fetch_queue import start_fetch_worker, stop_fetch_worker
from app.services.rate_limiter import cleanup_rate_limiter
from app.services.telegram_client import cleanup_telegram_client
from app.services.telegram_updates import start_update_handler, stop_update_handler
from app.tracing import setup_tracing

# Configure structured logging
configure_logging()
logger = structlog.get_logger(__name__)

settings = get_settings()
scheduler = AsyncIOScheduler()
scheduler_lock_id = str(uuid.uuid4())
scheduler_lock_renew_task = None


async def renew_scheduler_lock(redis_client: Redis, lock_key: str, lock_id: str):
    """Periodically renew the scheduler lock to maintain ownership."""
    while True:
        try:
            await asyncio.sleep(60)
            # Renew lock with 300s TTL (5 minutes)
            script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """
            result = await redis_client.eval(script, 1, lock_key, lock_id, 300)
            if result == 1:
                logger.debug("Scheduler lock renewed", lock_id=lock_id)
            else:
                logger.warning("Failed to renew scheduler lock - lock lost", lock_id=lock_id)
                break
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error renewing scheduler lock: {type(e).__name__}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler_lock_renew_task

    # Initialize Sentry (before other startup)
    if settings.sentry_dsn:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[FastApiIntegration()],
            sample_rate=1.0,
            traces_sample_rate=settings.sentry_traces_sample_rate,
        )
        logger.info("Sentry initialized")

    redis_cache = None
    redis_lock_client = None
    scheduler_started = False

    # Startup: Initialize database
    await init_db()
    logger.info("Database initialized")

    # Seed curated collections
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await seed_curated_collections(session)
    logger.info("Curated collections seeded")

    await start_fetch_worker()
    await start_update_handler()

    if settings.enable_response_cache and settings.redis_url:
        try:
            redis_cache = Redis.from_url(settings.redis_url)
            FastAPICache.init(RedisBackend(redis_cache), prefix="osfeed-api-cache")
            logger.info("Response cache initialized")
        except RedisError as e:
            logger.error(f"Failed to initialize Redis cache: {type(e).__name__}: {e}")
            redis_cache = None
    elif settings.enable_response_cache:
        logger.warning("Response cache enabled but REDIS_URL is missing; caching disabled")

    # Start background jobs with distributed lock
    if settings.scheduler_enabled:
        lock_acquired = False
        lock_key = "osfeed:scheduler_lock"

        # Try to acquire Redis lock if available
        if settings.redis_url:
            try:
                redis_lock_client = Redis.from_url(settings.redis_url)
                # Try to acquire lock with SET NX EX 300 (5 minutes TTL)
                lock_acquired = await redis_lock_client.set(
                    lock_key, scheduler_lock_id, nx=True, ex=300
                )
                if lock_acquired:
                    logger.info("Scheduler lock acquired", lock_id=scheduler_lock_id)
                else:
                    logger.info("Scheduler lock not acquired - another worker is running jobs")
            except RedisError as e:
                logger.warning(
                    f"Failed to connect to Redis for scheduler lock: {type(e).__name__}: {e}. "
                    "Falling back to starting scheduler anyway."
                )
                lock_acquired = True  # Fallback: start scheduler if Redis unavailable
        else:
            logger.warning("REDIS_URL not set - starting scheduler without distributed lock")
            lock_acquired = True  # Fallback: start scheduler if Redis not configured

        if lock_acquired:
            # Collect messages every 5 minutes
            scheduler.add_job(collect_messages_job, 'interval', minutes=5, id='collect_messages')

            # Purge audit logs based on retention settings
            purge_hour, purge_minute = map(int, settings.audit_log_purge_time.split(':'))
            scheduler.add_job(purge_audit_logs_job, 'cron', hour=purge_hour, minute=purge_minute, id='purge_audit_logs')

            scheduler.add_job(evaluate_alerts_job, 'interval', minutes=2, id='alert_monitor')

            # Process JoinChannel queue at midnight UTC
            scheduler.add_job(
                process_join_queue,
                'cron',
                hour=0,
                minute=0,
                timezone='UTC',
                id='process_join_queue'
            )

            scheduler.add_job(
                translate_pending_messages_job,
                'interval',
                minutes=1,
                id='translate_pending_messages',
            )

            scheduler.add_job(score_relevance_job, 'interval', minutes=5, id='score_relevance')

            scheduler.add_job(score_escalation_job, 'interval', minutes=5, id='score_escalation')

            scheduler.add_job(correlate_sources_job, 'interval', minutes=10, id='correlate_sources')

            scheduler.add_job(detect_patterns_job, 'interval', minutes=15, id='detect_patterns')

            scheduler.add_job(send_daily_digests_job, 'cron', minute=5, id='send_daily_digests')

            scheduler.start()
            scheduler_started = True
            logger.info("Background jobs scheduled (collecting every 5 minutes, translating every 1 minute)")

            # Start lock renewal task if using Redis
            if redis_lock_client:
                scheduler_lock_renew_task = asyncio.create_task(
                    renew_scheduler_lock(redis_lock_client, lock_key, scheduler_lock_id)
                )
                logger.info("Scheduler lock renewal task started")

    yield

    # Shutdown
    if settings.scheduler_enabled and scheduler_started:
        scheduler.shutdown()
        logger.info("Scheduler shut down")

    # Cancel lock renewal task if running
    if scheduler_lock_renew_task and not scheduler_lock_renew_task.done():
        scheduler_lock_renew_task.cancel()
        try:
            await scheduler_lock_renew_task
        except asyncio.CancelledError:
            pass
        logger.info("Scheduler lock renewal task cancelled")

    # Release scheduler lock
    if redis_lock_client:
        try:
            # Only release if we still own the lock
            script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            result = await redis_lock_client.eval(script, 1, "osfeed:scheduler_lock", scheduler_lock_id)
            if result == 1:
                logger.info("Scheduler lock released", lock_id=scheduler_lock_id)
            await redis_lock_client.close()
            await redis_lock_client.connection_pool.disconnect()
        except Exception as e:
            logger.error(f"Error releasing scheduler lock: {type(e).__name__}: {e}")

    await stop_fetch_worker()
    await stop_update_handler()
    await cleanup_telegram_client()
    await cleanup_rate_limiter()
    if redis_cache:
        await redis_cache.close()
        await redis_cache.connection_pool.disconnect()
    logger.info("Shutting down...")


app = FastAPI(
    title="OSFeed API",
    description="Intelligent Telegram Aggregator with AI-powered translation and summarization",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if settings.app_env == "production" else "/docs",
    redoc_url=None if settings.app_env == "production" else "/redoc",
    openapi_url=None if settings.app_env == "production" else "/openapi.json",
)

# Prometheus metrics
if settings.prometheus_enabled:
    from prometheus_fastapi_instrumentator import Instrumentator

    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# OpenTelemetry tracing
setup_tracing(app)

# CORS middleware - allow both www and non-www versions
cors_origins = [
    settings.frontend_url,
    "http://localhost:5173",
]
# Add www variant if frontend_url doesn't have www
if "://www." not in settings.frontend_url:
    cors_origins.append(settings.frontend_url.replace("://", "://www."))
# Add non-www variant if frontend_url has www
elif "://www." in settings.frontend_url:
    cors_origins.append(settings.frontend_url.replace("://www.", "://"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Auth middleware (inner — runs first on requests, after security headers on responses)
app.add_middleware(AuthMiddleware)

# Request ID middleware (between auth and security headers)
app.add_middleware(RequestIdMiddleware)

# Security headers middleware (outer — added last so it wraps all responses including auth 401s)
app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(channels.router, prefix="/api/channels", tags=["channels"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(collections.router, prefix="/api/collections", tags=["collections"])
app.include_router(audit_logs.router, prefix="/api/audit-logs", tags=["audit-logs"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(contact_sales.router, prefix="/api", tags=["contact-sales"])
app.include_router(stripe.router, prefix="/api", tags=["stripe"])
app.include_router(newsletter.router, prefix="/api", tags=["newsletter"])
app.include_router(summaries.router, prefix="/api/summaries", tags=["summaries"])
app.include_router(digests.router, prefix="/api/digests", tags=["digests"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(subscription.router, prefix="/api/subscription", tags=["subscription"])


@app.get("/")
async def root():
    if settings.app_env == "production":
        return {"status": "ok"}
    return {
        "message": "OSFeed API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint that verifies database connectivity."""
    from fastapi.responses import JSONResponse
    from sqlalchemy import text

    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except SQLAlchemyError as e:
        logger.warning(f"Health check failed: {type(e).__name__}: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected"}
        )
    except (OSError, ConnectionError, TimeoutError) as e:
        logger.warning(f"Health check failed with connection error: {type(e).__name__}: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected"}
        )
    except Exception as e:
        logger.warning(f"Health check failed with unexpected error: {type(e).__name__}: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected"}
        )
