from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from app.config import get_settings
from app.database import init_db
from app.api import channels, messages, summaries, auth, collections, audit_logs, stats
from app.jobs.collect_messages import collect_messages_job
from app.jobs.generate_summaries import generate_summaries_job
from app.jobs.purge_audit_logs import purge_audit_logs_job

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
    # Startup: Initialize database
    await init_db()
    print("Database initialized")

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

        scheduler.start()
        print("Background jobs scheduled (collecting every 2 minutes)")

    yield

    # Shutdown
    if settings.scheduler_enabled:
        scheduler.shutdown()
    print("Shutting down...")


app = FastAPI(
    title="TeleScope API",
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


@app.get("/")
async def root():
    return {
        "message": "TeleScope API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
