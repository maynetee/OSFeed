import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.jobs.retry import retry
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)
settings = get_settings()


@retry(max_attempts=3)
async def purge_audit_logs_job() -> None:
    retention_days = settings.audit_log_retention_days
    if retention_days <= 0:
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            delete(AuditLog).where(AuditLog.created_at < cutoff)
        )
        await session.commit()
        if result.rowcount:
            logger.info("Purged %s audit logs older than %s days", result.rowcount, retention_days)
