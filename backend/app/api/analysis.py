"""API routes for intelligence analysis features: escalation, correlation, patterns, timelines."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.users import current_active_user
from app.database import get_db
from app.models.analysis import Correlation, DetectedPattern, EscalationScore, Timeline
from app.models.message import Message
from app.models.user import User
from app.schemas.analysis import (
    CorrelationListResponse,
    CorrelationResponse,
    DetectedPatternResponse,
    EscalationTrendPoint,
    EscalationTrendResponse,
    PatternListResponse,
    TimelineGenerateRequest,
    TimelineListResponse,
    TimelineResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# === Escalation Endpoints ===

@router.get("/escalation", response_model=EscalationTrendResponse)
async def get_escalation_trend(
    collection_id: Optional[UUID] = None,
    period: str = Query("7d", regex="^(7d|30d|90d)$"),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get escalation trend data for a given period."""
    days = {"7d": 7, "30d": 30, "90d": 90}[period]
    since = datetime.now(timezone.utc) - timedelta(days=days)

    query = (
        select(
            func.date(Message.published_at).label("day"),
            func.count().filter(EscalationScore.level == "high").label("high_count"),
            func.count().filter(EscalationScore.level == "medium").label("medium_count"),
            func.count().filter(EscalationScore.level == "low").label("low_count"),
            func.avg(EscalationScore.score).label("avg_score"),
        )
        .join(EscalationScore, EscalationScore.message_id == Message.id)
        .where(Message.published_at >= since)
        .group_by(func.date(Message.published_at))
        .order_by(func.date(Message.published_at))
    )

    if collection_id:
        from app.models.channel import Channel
        from app.models.collection import collection_channels
        query = query.join(Channel, Channel.id == Message.channel_id).join(
            collection_channels,
            collection_channels.c.channel_id == Channel.id,
        ).where(collection_channels.c.collection_id == collection_id)

    result = await db.execute(query)
    rows = result.all()

    trend = []
    total_high = total_medium = total_low = 0
    for row in rows:
        point = EscalationTrendPoint(
            date=str(row.day),
            high_count=row.high_count or 0,
            medium_count=row.medium_count or 0,
            low_count=row.low_count or 0,
            avg_score=round(float(row.avg_score or 0), 3),
        )
        trend.append(point)
        total_high += point.high_count
        total_medium += point.medium_count
        total_low += point.low_count

    return EscalationTrendResponse(
        period=period,
        trend=trend,
        total_high=total_high,
        total_medium=total_medium,
        total_low=total_low,
    )


# === Correlation Endpoints ===

@router.get("/correlations", response_model=CorrelationListResponse)
async def list_correlations(
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent cross-source correlation analyses."""
    query = select(Correlation).order_by(desc(Correlation.created_at)).limit(limit)
    result = await db.execute(query)
    correlations = result.scalars().all()

    return CorrelationListResponse(
        correlations=[CorrelationResponse.model_validate(c) for c in correlations],
        total=len(correlations),
    )


@router.get("/correlations/{duplicate_group_id}", response_model=CorrelationResponse)
async def get_correlation(
    duplicate_group_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get cross-source correlation for a specific duplicate group."""
    result = await db.execute(
        select(Correlation).where(Correlation.duplicate_group_id == duplicate_group_id)
    )
    correlation = result.scalar_one_or_none()
    if not correlation:
        raise HTTPException(status_code=404, detail="Correlation not found")
    return CorrelationResponse.model_validate(correlation)


# === Pattern Detection Endpoints ===

@router.get("/patterns", response_model=PatternListResponse)
async def list_patterns(
    period: str = Query("7d", regex="^(7d|30d)$"),
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recently detected intelligence patterns."""
    days = {"7d": 7, "30d": 30}[period]
    since = datetime.now(timezone.utc) - timedelta(days=days)

    query = (
        select(DetectedPattern)
        .where(DetectedPattern.detected_at >= since)
        .order_by(desc(DetectedPattern.detected_at))
        .limit(limit)
    )
    result = await db.execute(query)
    patterns = result.scalars().all()

    return PatternListResponse(
        patterns=[DetectedPatternResponse.model_validate(p) for p in patterns],
        total=len(patterns),
    )


@router.get("/patterns/{pattern_id}", response_model=DetectedPatternResponse)
async def get_pattern(
    pattern_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific detected pattern with evidence."""
    result = await db.execute(
        select(DetectedPattern).where(DetectedPattern.id == pattern_id)
    )
    pattern = result.scalar_one_or_none()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return DetectedPatternResponse.model_validate(pattern)


# === Timeline Endpoints ===

@router.post("/timeline/generate", response_model=TimelineResponse)
async def generate_timeline(
    request: TimelineGenerateRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a timeline reconstruction from intelligence messages."""
    from app.services.timeline_service import timeline_service

    if not request.topic and not request.collection_id:
        raise HTTPException(status_code=400, detail="Either topic or collection_id is required")

    timeline = await timeline_service.generate_timeline(
        user_id=user.id,
        topic=request.topic,
        collection_id=request.collection_id,
        start_date=request.start_date,
        end_date=request.end_date,
        db=db,
    )
    return TimelineResponse.model_validate(timeline)


@router.get("/timelines", response_model=TimelineListResponse)
async def list_timelines(
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's generated timelines."""
    query = (
        select(Timeline)
        .where(Timeline.user_id == user.id)
        .order_by(desc(Timeline.created_at))
        .limit(limit)
    )
    result = await db.execute(query)
    timelines = result.scalars().all()

    return TimelineListResponse(
        timelines=[TimelineResponse.model_validate(t) for t in timelines],
        total=len(timelines),
    )


@router.get("/timelines/{timeline_id}", response_model=TimelineResponse)
async def get_timeline(
    timeline_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific timeline."""
    result = await db.execute(
        select(Timeline).where(Timeline.id == timeline_id, Timeline.user_id == user.id)
    )
    timeline = result.scalar_one_or_none()
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return TimelineResponse.model_validate(timeline)


@router.delete("/timelines/{timeline_id}")
async def delete_timeline(
    timeline_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user's timeline."""
    result = await db.execute(
        select(Timeline).where(Timeline.id == timeline_id, Timeline.user_id == user.id)
    )
    timeline = result.scalar_one_or_none()
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    await db.delete(timeline)
    return {"detail": "Timeline deleted"}
