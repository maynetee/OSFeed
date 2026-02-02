from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, List
from uuid import UUID
import logging

from app.database import get_db
from app.models.alert import Alert, AlertTrigger
from app.models.collection import Collection
from app.models.collection_share import CollectionShare
from app.models.user import User
from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate, AlertTriggerResponse
from app.auth.users import current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()


def _assert_permission(collection: Collection, user: User, permission: Optional[str], action: str) -> None:
    if collection.user_id == user.id:
        return
    if action == "view" and permission:
        return
    if action == "edit" and permission in {"editor", "admin"}:
        return
    if action == "delete" and permission == "admin":
        return
    raise HTTPException(status_code=403, detail="Not authorized")


async def _get_collection_for_user(
    db: AsyncSession,
    collection_id: UUID,
    user_id: UUID,
):
    result = await db.execute(
        select(Collection, CollectionShare.permission)
        .outerjoin(
            CollectionShare,
            (CollectionShare.collection_id == Collection.id) & (CollectionShare.user_id == user_id),
        )
        .where(Collection.id == collection_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Collection not found")
    return row


@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    collection_id: Optional[UUID] = None,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all alerts for the current user, optionally filtered by collection."""
    query = select(Alert).where(Alert.user_id == user.id)
    if collection_id:
        query = query.where(Alert.collection_id == collection_id)
    result = await db.execute(query.order_by(desc(Alert.created_at)))
    return result.scalars().all()


@router.post("", response_model=AlertResponse)
async def create_alert(
    payload: AlertCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new alert for a collection with specified keywords and entities."""
    try:
        collection, permission = await _get_collection_for_user(db, payload.collection_id, user.id)
        _assert_permission(collection, user, permission, "edit")

        alert = Alert(
            collection_id=payload.collection_id,
            user_id=user.id,
            name=payload.name,
            keywords=payload.keywords or [],
            entities=payload.entities or [],
            min_threshold=payload.min_threshold,
            frequency=payload.frequency,
            notification_channels=payload.notification_channels or ["in_app"],
            is_active=payload.is_active,
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert for user {user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create alert")


@router.get("/triggers/recent", response_model=List[AlertTriggerResponse])
async def list_recent_triggers(
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List recent alert triggers across all of the user's alerts."""
    result = await db.execute(
        select(AlertTrigger)
        .join(Alert, AlertTrigger.alert_id == Alert.id)
        .where(Alert.user_id == user.id)
        .order_by(desc(AlertTrigger.triggered_at))
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific alert by ID."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: UUID,
    payload: AlertUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing alert's configuration."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    data = payload.dict(exclude_unset=True)
    if data.get("collection_id"):
        collection, permission = await _get_collection_for_user(db, data["collection_id"], user.id)
        _assert_permission(collection, user, permission, "edit")
    for key, value in data.items():
        setattr(alert, key, value)

    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an alert permanently."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.delete(alert)
    await db.commit()
    return {"message": "Alert deleted"}


@router.get("/{alert_id}/triggers", response_model=List[AlertTriggerResponse])
async def list_alert_triggers(
    alert_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all triggers for a specific alert."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    triggers_result = await db.execute(
        select(AlertTrigger)
        .where(AlertTrigger.alert_id == alert_id)
        .order_by(desc(AlertTrigger.triggered_at))
        .limit(limit)
    )
    return triggers_result.scalars().all()
