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
from app.api import channels, messages, summaries, auth, collections, audit_logs, stats, alerts, intelligence
from app.jobs.collect_messages import collect_messages_job
from app.jobs.generate_summaries import generate_summaries_job
from app.jobs.translate_pending_messages import translate_pending_messages_job
from app.jobs.purge_audit_logs import purge_audit_logs_job
from app.jobs.alerts import evaluate_alerts_job
from app.jobs.clustering import run_clustering_job
from app.jobs.ner_extraction import run_ner_job
from app.services.fetch_queue import start_fetch_worker, stop_fetch_worker

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
        # Collect messages every 2 minutes (job takes ~90 seconds to complete)
        scheduler.add_job(collect_messages_job, 'interval', minutes=2, id='collect_messages')

        # Generate daily summary at configured time
        hour, minute = map(int, settings.summary_time.split(':'))
        scheduler.add_job(generate_summaries_job, 'cron', hour=hour, minute=minute, id='daily_summary')

        # Purge audit logs based on retention settings
        purge_hour, purge_minute = map(int, settings.audit_log_purge_time.split(':'))
        scheduler.add_job(purge_audit_logs_job, 'cron', hour=purge_hour, minute=purge_minute, id='purge_audit_logs')

        scheduler.add_job(evaluate_alerts_job, 'interval', minutes=10, id='alert_monitor')

        scheduler.add_job(
            translate_pending_messages_job,
            'interval',
            minutes=5,
            id='translate_pending_messages',
        )

        scheduler.add_job(
            run_clustering_job,
            'interval',
            minutes=60,
            id='clustering_job',
        )

        scheduler.add_job(
            run_ner_job,
            'interval',
            minutes=60,
            id='ner_job',
        )

        scheduler.start()
        logger.info("Background jobs scheduled (collecting every 2 minutes)")

    yield

    # Shutdown
    if settings.scheduler_enabled:
        scheduler.shutdown()
    await stop_fetch_worker()
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(channels.router, prefix="/api/channels", tags=["channels"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(summaries.router, prefix="/api/summaries", tags=["summaries"])
app.include_router(collections.router, prefix="/api/collections", tags=["collections"])
app.include_router(audit_logs.router, prefix="/api/audit-logs", tags=["audit-logs"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(intelligence.router, prefix="/api/intelligence", tags=["intelligence"])


@app.get("/")
async def root():
    return {
        "message": "OSFeed API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
