import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app.api import alerts, analysis, audit_logs, auth, channels, collections, contact_sales, digests, insights, messages, newsletter, notifications, stats, stripe, summaries
from app.config import get_settings
from app.database import get_engine, init_db
from app.jobs.alerts import evaluate_alerts_job
from app.jobs.collect_messages import collect_messages_job
from app.jobs.detect_patterns import detect_patterns_job
from app.jobs.purge_audit_logs import purge_audit_logs_job
from app.jobs.correlate_sources import correlate_sources_job
from app.jobs.score_escalation import score_escalation_job
from app.jobs.score_relevance import score_relevance_job
from app.jobs.send_daily_digests import send_daily_digests_job
from app.jobs.translate_pending_messages import translate_pending_messages_job
from app.middleware.auth import AuthMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.seeds.curated_collections import seed_curated_collections
from app.services.channel_join_queue import process_join_queue
from app.services.fetch_queue import start_fetch_worker, stop_fetch_worker
from app.services.rate_limiter import cleanup_rate_limiter
from app.services.telegram_client import cleanup_telegram_client
from app.services.telegram_updates import start_update_handler, stop_update_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_cache = None
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

    # Start background jobs
    if settings.scheduler_enabled:
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
        logger.info("Background jobs scheduled (collecting every 5 minutes, translating every 1 minute)")

    yield

    # Shutdown
    if settings.scheduler_enabled:
        scheduler.shutdown()
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

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Auth middleware (added after SecurityHeaders so it executes first in reverse order)
app.add_middleware(AuthMiddleware)

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
