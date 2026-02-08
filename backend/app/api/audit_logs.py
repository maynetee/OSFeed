"""Audit logs API routes for OSFeed."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from typing import Optional, List

from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.auth.users import current_active_user

router = APIRouter()


@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=200),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve audit logs for the current user with optional filtering by action, resource type, and date range."""
    query = select(AuditLog).where(AuditLog.user_id == user.id)

    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)

    query = query.order_by(desc(AuditLog.created_at)).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    return logs
