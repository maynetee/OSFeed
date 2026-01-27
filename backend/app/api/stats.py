from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, and_
from datetime import datetime, timedelta, timezone
import csv
from io import StringIO
from uuid import UUID

from app.database import get_db
from app.models.message import Message, MessageTranslation
from app.models.channel import Channel
from app.models.summary import Summary
from app.models.user import User
from app.models.api_usage import ApiUsage
from app.auth.users import current_active_user
from app.config import get_settings
from app.utils.response_cache import response_cache

router = APIRouter()
settings = get_settings()


@router.get("/overview")
@response_cache(expire=settings.response_cache_ttl, namespace="stats-overview")
async def get_overview_stats(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)

    # Base filter for user isolation
    from app.models.channel import user_channels
    
    # Helper to apply user filter
    def apply_user_filter(query, join_target=Message):
        if join_target == Message:
            return query.join(Channel, Message.channel_id == Channel.id).join(
                user_channels, 
                and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user.id)
            )
        elif join_target == Channel:
            return query.join(
                user_channels,
                and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user.id)
            )
        return query

    # Total messages (user scoped)
    total_messages_query = apply_user_filter(select(func.count()).select_from(Message))
    total_messages = await db.execute(total_messages_query)
    
    # Active channels (user scoped)
    total_channels_query = apply_user_filter(select(func.count()).select_from(Channel), join_target=Channel)
    total_channels = await db.execute(total_channels_query.where(Channel.is_active == True))

    # Messages 24h (user scoped)
    messages_24h_query = apply_user_filter(select(func.count()).select_from(Message))
    messages_24h = await db.execute(messages_24h_query.where(Message.published_at >= day_ago))

    # Duplicates 24h (user scoped)
    duplicates_24h_query = apply_user_filter(select(func.count()).select_from(Message))
    duplicates_24h = await db.execute(
        duplicates_24h_query
        .where(Message.published_at >= day_ago)
        .where(Message.is_duplicate == True)
    )

    # Summaries (user scoped via collections or implicit channel access - simpler to just count global for now or filter by user's collections, 
    # but Summary model logic might be different. For safely, let's keep it global or fix later if needed, 
    # but the task is about messages/channels. Let's assume summaries are system-wide or per-collection which user owns.)
    summaries_total = await db.execute(select(func.count()).select_from(Summary))

    return {
        "total_messages": total_messages.scalar() or 0,
        "active_channels": total_channels.scalar() or 0,
        "messages_last_24h": messages_24h.scalar() or 0,
        "duplicates_last_24h": duplicates_24h.scalar() or 0,
        "summaries_total": summaries_total.scalar() or 0,
    }


@router.get("/messages-by-day")
@response_cache(expire=settings.response_cache_ttl, namespace="stats-messages-by-day")
async def get_messages_by_day(
    days: int = Query(7, ge=1, le=90),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    date_bucket = func.date(Message.published_at)

    from app.models.channel import user_channels

    result = await db.execute(
        select(date_bucket.label("day"), func.count().label("count"))
        .join(Channel, Message.channel_id == Channel.id)
        .join(user_channels, and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user.id))
        .where(Message.published_at >= start_date)
        .group_by(date_bucket)
        .order_by(date_bucket)
    )
    rows = result.all()
    return [{"date": str(row.day), "count": row.count} for row in rows]


@router.get("/messages-by-channel")
@response_cache(expire=settings.response_cache_ttl, namespace="stats-messages-by-channel")
async def get_messages_by_channel(
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.channel import user_channels

    result = await db.execute(
        select(Channel.id, Channel.title, func.count(Message.id).label("count"))
        .join(user_channels, and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user.id))
        .join(Message, Message.channel_id == Channel.id)
        .group_by(Channel.id, Channel.title)
        .order_by(desc("count"))
        .limit(limit)
    )
    rows = result.all()
    return [{"channel_id": row.id, "channel_title": row.title, "count": row.count} for row in rows]


@router.get("/export/csv")
async def export_stats_csv(
    days: int = Query(7, ge=1, le=90),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    overview = await get_overview_stats(user=user, db=db)
    by_day = await get_messages_by_day(days=days, user=user, db=db)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["metric", "value"])
    for key, value in overview.items():
        writer.writerow([key, value])
    writer.writerow([])
    writer.writerow(["date", "message_count"])
    for row in by_day:
        writer.writerow([row["date"], row["count"]])

    output.seek(0)
    filename = "osfeed-stats.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/trust")
@response_cache(expire=settings.response_cache_ttl, namespace="stats-trust")
async def get_trust_stats(
    channel_ids: Optional[List[UUID]] = Query(None),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)

    filters = [Message.published_at >= day_ago]
    if channel_ids:
        filters.append(Message.channel_id.in_(channel_ids))

    total_result = await db.execute(
        select(func.count()).select_from(Message).where(*filters)
    )
    total_messages = total_result.scalar() or 0

    primary_result = await db.execute(
        select(func.count())
        .select_from(Message)
        .where(*filters)
        .where(Message.is_duplicate == False)
        .where(or_(Message.originality_score.is_(None), Message.originality_score >= 90))
    )
    propaganda_result = await db.execute(
        select(func.count())
        .select_from(Message)
        .where(*filters)
        .where(Message.is_duplicate == True)
        .where(Message.originality_score <= 20)
    )
    verified_result = await db.execute(
        select(func.count(func.distinct(Message.channel_id)))
        .select_from(Message)
        .where(*filters)
    )

    primary_count = primary_result.scalar() or 0
    propaganda_count = propaganda_result.scalar() or 0
    verified_channels = verified_result.scalar() or 0

    primary_rate = round((primary_count / total_messages) * 100, 1) if total_messages else 0.0
    propaganda_rate = round((propaganda_count / total_messages) * 100, 1) if total_messages else 0.0

    return {
        "primary_sources_rate": primary_rate,
        "propaganda_rate": propaganda_rate,
        "verified_channels": verified_channels,
        "total_messages_24h": total_messages,
    }


@router.get("/api-usage")
@response_cache(expire=settings.response_cache_ttl, namespace="stats-api-usage")
async def get_api_usage_stats(
    days: int = Query(7, ge=1, le=365),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    totals_result = await db.execute(
        select(
            func.coalesce(func.sum(ApiUsage.total_tokens), 0),
            func.coalesce(func.sum(ApiUsage.estimated_cost_usd), 0),
        ).where(ApiUsage.created_at >= start_date)
    )
    total_tokens, total_cost = totals_result.first()

    tokens_sum = func.coalesce(func.sum(ApiUsage.total_tokens), 0).label("tokens")
    cost_sum = func.coalesce(func.sum(ApiUsage.estimated_cost_usd), 0).label("cost")
    breakdown_result = await db.execute(
        select(
            ApiUsage.provider,
            ApiUsage.model,
            ApiUsage.purpose,
            tokens_sum,
            cost_sum,
        )
        .where(ApiUsage.created_at >= start_date)
        .group_by(ApiUsage.provider, ApiUsage.model, ApiUsage.purpose)
        .order_by(desc(cost_sum))
    )
    breakdown = [
        {
            "provider": row.provider,
            "model": row.model,
            "purpose": row.purpose,
            "total_tokens": int(row.tokens or 0),
            "estimated_cost_usd": float(row.cost or 0),
        }
        for row in breakdown_result.all()
    ]

    return {
        "window_days": days,
        "total_tokens": int(total_tokens or 0),
        "estimated_cost_usd": float(total_cost or 0),
        "breakdown": breakdown,
    }

@router.get("/translation-metrics")
@response_cache(expire=settings.response_cache_ttl, namespace="stats-translation")
async def get_translation_metrics(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Total translations in cache
    total_result = await db.execute(select(func.count()).select_from(MessageTranslation))
    total_cached = total_result.scalar() or 0

    # Total tokens saved (tokens stored in cache)
    tokens_result = await db.execute(
        select(func.sum(MessageTranslation.token_count)).select_from(MessageTranslation)
    )
    tokens_saved = tokens_result.scalar() or 0

    # Current implementation doesn't track hit counts in DB (only in Redis per-key)
    # So we return placeholder values for now
    hits = 0
    hit_rate = 0.0

    return {
        "total_translations": total_cached,
        "cache_hits": hits,
        "cache_hit_rate": hit_rate,
        "tokens_saved": tokens_saved,
    }
