from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, update
from typing import Optional
from uuid import UUID
import logging

from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationListResponse
from app.auth.users import current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    is_read: Optional[bool] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List notifications for the current user with optional read/unread filter."""
    query = select(Notification).where(Notification.user_id == user.id)
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)

    # Get total count
    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total = (await db.execute(count_query)).scalar() or 0

    # Get unread count
    unread_count = (await db.execute(
        select(func.count()).where(
            Notification.user_id == user.id,
            Notification.is_read == False,  # noqa: E712
        )
    )).scalar() or 0

    # Get paginated results
    result = await db.execute(
        query.order_by(desc(Notification.created_at))
        .limit(limit)
        .offset(offset)
    )
    notifications = result.scalars().all()

    return NotificationListResponse(
        notifications=notifications,
        unread_count=unread_count,
        total=total,
    )


@router.get("/unread-count")
async def get_unread_count(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the count of unread notifications."""
    count = (await db.execute(
        select(func.count()).where(
            Notification.user_id == user.id,
            Notification.is_read == False,  # noqa: E712
        )
    )).scalar() or 0
    return {"count": count}


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a single notification as read."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification


@router.post("/mark-all-read")
async def mark_all_read(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read for the current user."""
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == user.id,
            Notification.is_read == False,  # noqa: E712
        )
        .values(is_read=True)
    )
    await db.commit()
    return {"message": "All notifications marked as read"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a notification."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    await db.delete(notification)
    await db.commit()
    return {"message": "Notification deleted"}
