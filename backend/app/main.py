from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
from redis.asyncio import Redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from app.config import get_settings
from app.database import init_db
from app.api import channels, messages, auth, collections, audit_logs, stats, alerts
from app.jobs.collect_messages import collect_messages_job
from app.jobs.translate_pending_messages import translate_pending_messages_job
from app.jobs.purge_audit_logs import purge_audit_logs_job
from app.jobs.alerts import evaluate_alerts_job
from app.services.fetch_queue import start_fetch_worker, stop_fetch_worker
from app.services.telegram_client import cleanup_telegram_client
from app.services.rate_limiter import cleanup_rate_limiter
from app.services.channel_join_queue import process_join_queue
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

    await start_fetch_worker()
    await start_update_handler()

    if settings.enable_response_cache and settings.redis_url:
        try:
            redis_cache = Redis.from_url(settings.redis_url)
            FastAPICache.init(RedisBackend(redis_cache), prefix="osfeed-api-cache")
            logger.info("Response cache initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
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

        scheduler.add_job(evaluate_alerts_job, 'interval', minutes=10, id='alert_monitor')

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
            minutes=5,
            id='translate_pending_messages',
        )

        scheduler.start()
        logger.info("Background jobs scheduled (collecting every 5 minutes)")

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

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(channels.router, prefix="/api/channels", tags=["channels"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(collections.router, prefix="/api/collections", tags=["collections"])
app.include_router(audit_logs.router, prefix="/api/audit-logs", tags=["audit-logs"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])


@app.get("/")
async def root():
    return {
        "message": "OSFeed API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint that verifies database connectivity."""
    from app.database import get_engine
    from sqlalchemy import text
    from fastapi.responses import JSONResponse

    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )
