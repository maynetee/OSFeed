from typing import List, Optional
import asyncio

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, and_, case
from datetime import datetime, timedelta, timezone
import csv
from io import StringIO
from uuid import UUID
from typing import List

from pydantic import BaseModel, Field

from app.database import get_db
from app.models.message import Message, MessageTranslation
from app.models.channel import Channel
from app.models.collection import Collection, collection_channels
from app.models.collection_share import CollectionShare
from app.models.user import User
from app.models.api_usage import ApiUsage
from app.auth.users import current_active_user
from app.config import get_settings
from app.utils.response_cache import response_cache
from app.schemas.stats import DashboardResponse
from app.schemas.channel import ChannelResponse
from app.schemas.collection import CollectionResponse
from sqlalchemy.orm import selectinload

router = APIRouter()
settings = get_settings()


async def get_user_channels(user: User, db: AsyncSession) -> List[ChannelResponse]:
    """Fetch all active channels for the user."""
    from app.models.channel import user_channels

    result = await db.execute(
        select(Channel)
        .join(user_channels, Channel.id == user_channels.c.channel_id)
        .where(
            and_(
                user_channels.c.user_id == user.id,
                Channel.is_active == True
            )
        )
    )
    channels = result.scalars().all()
    return [ChannelResponse.model_validate(channel) for channel in channels]


async def get_user_collections(user: User, db: AsyncSession) -> List[CollectionResponse]:
    """Fetch all collections owned by or shared with the user."""
    # Step 1: Fetch user's collections with channels loaded for non-global collections
    result = await db.execute(
        select(Collection)
        .options(selectinload(Collection.channels))
        .outerjoin(
            CollectionShare,
            (CollectionShare.collection_id == Collection.id) & (CollectionShare.user_id == user.id),
        )
        .where(or_(Collection.user_id == user.id, CollectionShare.user_id == user.id))
    )
    collections = result.scalars().all()

    if not collections:
        return []

    # Step 2: Identify global collections
    has_global = any(c.is_global for c in collections)

    # Step 3: Load all active channel IDs once if any global collections exist
    all_active_channel_ids = []
    if has_global:
        all_active_channels_result = await db.execute(
            select(Channel.id).where(Channel.is_active == True)
        )
        all_active_channel_ids = [row[0] for row in all_active_channels_result.all()]

    # Step 4: Build responses using cached channel data
    responses = []
    for collection in collections:
        if collection.is_global:
            # Use cached all active channel IDs for global collections
            channel_ids = all_active_channel_ids
        else:
            # Use already-loaded channels from selectinload
            channel_ids = [channel.id for channel in collection.channels]

        responses.append(CollectionResponse(
            id=collection.id,
            user_id=collection.user_id,
            name=collection.name,
            description=collection.description,
            color=collection.color,
            icon=collection.icon,
            is_default=collection.is_default,
            is_global=collection.is_global,
            parent_id=collection.parent_id,
            auto_assign_languages=collection.auto_assign_languages or [],
            auto_assign_keywords=collection.auto_assign_keywords or [],
            auto_assign_tags=collection.auto_assign_tags or [],
            channel_ids=channel_ids,
            created_at=collection.created_at,
            updated_at=collection.updated_at,
        ))

    return responses


@router.get("/overview")
@response_cache(expire=settings.response_cache_ttl, namespace="stats-overview")
async def get_overview_stats(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get overview statistics for the authenticated user's channels.

    Returns key metrics including total message count across all time, number of active channels,
    message count from the last 24 hours, and duplicate message count from the last 24 hours.
    All statistics are filtered to only include channels the user has access to.
    """
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)

    # Base filter for user isolation
    from app.models.channel import user_channels

    # Consolidated message counts query using conditional aggregation
    messages_result = await db.execute(
        select(
            func.count().label("total_messages"),
            func.coalesce(
                func.sum(case((Message.published_at >= day_ago, 1), else_=0)),
                0
            ).label("messages_24h"),
            func.coalesce(
                func.sum(case((and_(Message.published_at >= day_ago, Message.is_duplicate == True), 1), else_=0)),
                0
            ).label("duplicates_24h"),
        )
        .select_from(Message)
        .join(Channel, Message.channel_id == Channel.id)
        .join(
            user_channels,
            and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user.id)
        )
    )
    messages_row = messages_result.first()

    # Active channels count (separate query as it's counting from a different table)
    total_channels_result = await db.execute(
        select(func.count())
        .select_from(Channel)
        .join(
            user_channels,
            and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user.id)
        )
        .where(Channel.is_active == True)
    )

    return {
        "total_messages": messages_row.total_messages if messages_row else 0,
        "active_channels": total_channels_result.scalar() or 0,
        "messages_last_24h": messages_row.messages_24h if messages_row else 0,
        "duplicates_last_24h": messages_row.duplicates_24h if messages_row else 0,
    }


@router.get("/dashboard", response_model=DashboardResponse)
@response_cache(expire=settings.response_cache_ttl, namespace="stats-dashboard")
async def get_dashboard_stats(
    days: int = Query(7, ge=1, le=90),
    channel_limit: int = Query(10, ge=1, le=50),
    collection_id: Optional[UUID] = Query(None),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive dashboard statistics aggregating multiple metrics for the authenticated user.

    Returns a unified response containing overview statistics, messages grouped by day over the specified
    time period (default 7 days, max 90 days), top channels by message count (default 10, max 50),
    trust metrics, API usage statistics, translation cache metrics, user's channels, and collections.
    All statistics are fetched in parallel using asyncio.gather for optimal performance.
    """
    # Fetch all stats in parallel using asyncio.gather
    overview, messages_by_day, messages_by_channel, trust, api_usage, translation, channels, collections = await asyncio.gather(
        get_overview_stats(user=user, db=db),
        get_messages_by_day(days=days, user=user, db=db),
        get_messages_by_channel(limit=channel_limit, user=user, db=db),
        get_trust_stats(channel_ids=None, user=user, db=db),
        get_api_usage_stats(days=days, user=user, db=db),
        get_translation_metrics(user=user, db=db),
        get_user_channels(user=user, db=db),
        get_user_collections(user=user, db=db),
    )

    return {
        "overview": overview,
        "messages_by_day": messages_by_day,
        "messages_by_channel": messages_by_channel,
        "trust_stats": trust,
        "api_usage": api_usage,
        "translation_metrics": translation,
        "channels": channels,
        "collections": collections,
    }


@router.get("/messages-by-day")
@response_cache(expire=settings.response_cache_ttl, namespace="stats-messages-by-day")
async def get_messages_by_day(
    days: int = Query(7, ge=1, le=90),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get daily message counts for the user's channels over a specified time period.

    Returns message counts grouped by day from the specified number of days ago until now
    (default 7 days, minimum 1 day, maximum 90 days). Each entry includes the date and
    total message count for that day, filtered to only include channels the user has access to.
    Results are ordered chronologically.
    """
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
    """
    Get message counts aggregated by channel, sorted by activity level.

    Returns the top channels by total message count (default 10 channels, minimum 1, maximum 50).
    Each entry includes the channel ID, channel title, and total message count across all time.
    Only includes channels the user has access to, sorted in descending order by message count
    to show the most active channels first.
    """
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
    """
    Export statistics to CSV format for external analysis or reporting.

    Returns a downloadable CSV file containing overview statistics (total messages, active channels,
    messages in last 24h, duplicates in last 24h) followed by daily message counts over the specified
    time period (default 7 days, minimum 1 day, maximum 90 days). All statistics are filtered to
    only include channels the user has access to. The file is named 'osfeed-stats.csv'.
    """
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


@router.get("/export/json")
async def export_stats_json(
    days: int = Query(7, ge=1, le=90),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export statistics to JSON format for programmatic consumption.

    Returns a JSON response containing overview statistics (total messages, active channels,
    messages in last 24h, duplicates in last 24h) and daily message counts over the specified
    time period (default 7 days, minimum 1 day, maximum 90 days). All statistics are filtered
    to only include channels the user has access to.
    """
    overview = await get_overview_stats(user=user, db=db)
    by_day = await get_messages_by_day(days=days, user=user, db=db)

    return {
        "overview": overview,
        "messages_by_day": by_day,
    }


@router.get("/trust")
@response_cache(expire=settings.response_cache_ttl, namespace="stats-trust")
async def get_trust_stats(
    channel_ids: Optional[List[UUID]] = Query(None),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get trust and content quality metrics for messages from the last 24 hours.

    Returns trust indicators including primary sources rate (percentage of non-duplicate messages
    with high originality score >= 90), propaganda rate (percentage of duplicate messages with
    low originality score <= 20), number of verified channels with activity, and total message
    count in the 24-hour window. Optionally filters by specific channel IDs. All statistics are
    filtered to only include channels the user has access to.
    """
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)

    # Base filter for user isolation
    from app.models.channel import user_channels

    # Build base query with user isolation
    base_query = (
        select(Message)
        .join(Channel, Message.channel_id == Channel.id)
        .join(
            user_channels,
            and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user.id)
        )
        .where(Message.published_at >= day_ago)
    )

    if channel_ids:
        base_query = base_query.where(Message.channel_id.in_(channel_ids))

    total_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total_messages = total_result.scalar() or 0

    # If specific channel_ids were requested but user has no access to any of them, return 404
    if channel_ids and total_messages == 0:
        raise HTTPException(status_code=404, detail="Channel not found")

    primary_result = await db.execute(
        select(func.count())
        .select_from(base_query.subquery())
        .where(
            and_(
                Message.is_duplicate == False,
                or_(Message.originality_score.is_(None), Message.originality_score >= 90)
            )
        )
    )
    propaganda_result = await db.execute(
        select(func.count())
        .select_from(base_query.subquery())
        .where(
            and_(
                Message.is_duplicate == True,
                Message.originality_score <= 20
            )
        )
    )
    verified_result = await db.execute(
        select(func.count(func.distinct(Message.channel_id)))
        .select_from(base_query.subquery())
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
    """
    Get API usage statistics and cost tracking over a specified time period.

    Returns total token consumption and estimated costs in USD over the specified number of days
    (default 7 days, minimum 1 day, maximum 365 days), along with a detailed breakdown by provider,
    model, and purpose. The breakdown is sorted by cost in descending order to highlight the most
    expensive API operations. Useful for monitoring and optimizing API expenses.
    """
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
    """
    Get translation cache performance metrics and efficiency statistics.

    Returns metrics about the translation caching system including total number of cached translations,
    cache hit count, cache miss count, calculated cache hit rate percentage, and total tokens saved
    by reusing cached translations instead of making new API calls. These metrics help monitor the
    effectiveness of translation caching in reducing API costs and improving response times.
    """
    # Total translations in cache
    total_result = await db.execute(select(func.count()).select_from(MessageTranslation))
    total_cached = total_result.scalar() or 0

    # Total tokens saved (tokens stored in cache)
    tokens_result = await db.execute(
        select(func.sum(MessageTranslation.token_count)).select_from(MessageTranslation)
    )
    tokens_saved = tokens_result.scalar() or 0

    # Read real cache hit/miss counters from Redis
    from app.services.cache import get_translation_cache_stats
    cache_stats = await get_translation_cache_stats()

    return {
        "total_translations": total_cached,
        "cache_hits": cache_stats["cache_hits"],
        "cache_misses": cache_stats["cache_misses"],
        "cache_hit_rate": cache_stats["cache_hit_rate"],
        "tokens_saved": tokens_saved,
    }


class BatchStatsRequest(BaseModel):
    collection_ids: List[UUID] = Field(..., max_length=50)


@router.post("/batch")
@response_cache(expire=settings.response_cache_ttl, namespace="stats-batch")
async def get_batch_stats(
    body: BatchStatsRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics for multiple collections efficiently in a single batch request.

    Accepts a list of collection IDs (maximum 50) and returns aggregated statistics for each collection
    including channel count, total message count across all time, message count from the last 24 hours,
    and message count from the last 7 days. Only returns data for collections the user owns or has
    access to via sharing. Uses optimized batch queries to minimize database round-trips and improve
    performance when fetching stats for multiple collections simultaneously.
    """
    collection_ids = body.collection_ids

    if not collection_ids:
        return {"stats": {}}

    # Verify user owns or has access to these collections
    from app.models.collection_share import CollectionShare

    result = await db.execute(
        select(Collection)
        .outerjoin(
            CollectionShare,
            (CollectionShare.collection_id == Collection.id) & (CollectionShare.user_id == user.id),
        )
        .where(
            Collection.id.in_(collection_ids),
            or_(Collection.user_id == user.id, CollectionShare.user_id == user.id),
        )
    )
    collections = result.scalars().all()
    accessible_ids = {c.id for c in collections}
    global_ids = {c.id for c in collections if c.is_global}
    non_global_ids = [cid for cid in accessible_ids if cid not in global_ids]

    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    # Build collection -> channel_ids mapping
    coll_channel_map: dict[UUID, list[UUID]] = {cid: [] for cid in accessible_ids}

    if non_global_ids:
        ch_result = await db.execute(
            select(
                collection_channels.c.collection_id,
                collection_channels.c.channel_id,
            ).where(collection_channels.c.collection_id.in_(non_global_ids))
        )
        for row in ch_result.all():
            coll_channel_map[row.collection_id].append(row.channel_id)

    if global_ids:
        active_ch_result = await db.execute(
            select(Channel.id).where(Channel.is_active == True)
        )
        all_active = [r[0] for r in active_ch_result.all()]
        for gid in global_ids:
            coll_channel_map[gid] = all_active

    # Gather all unique channel IDs for batch message queries
    all_channel_ids: set[UUID] = set()
    for ch_ids in coll_channel_map.values():
        all_channel_ids.update(ch_ids)

    # Batch query: message counts grouped by channel_id for different time windows
    channel_total: dict[UUID, int] = {}
    channel_24h: dict[UUID, int] = {}
    channel_7d: dict[UUID, int] = {}

    if all_channel_ids:
        # Total messages per channel
        total_result = await db.execute(
            select(Message.channel_id, func.count().label("cnt"))
            .where(Message.channel_id.in_(all_channel_ids))
            .group_by(Message.channel_id)
        )
        channel_total = {row.channel_id: row.cnt for row in total_result.all()}

        # 24h messages per channel
        result_24h = await db.execute(
            select(Message.channel_id, func.count().label("cnt"))
            .where(
                Message.channel_id.in_(all_channel_ids),
                Message.published_at >= day_ago,
            )
            .group_by(Message.channel_id)
        )
        channel_24h = {row.channel_id: row.cnt for row in result_24h.all()}

        # 7d messages per channel
        result_7d = await db.execute(
            select(Message.channel_id, func.count().label("cnt"))
            .where(
                Message.channel_id.in_(all_channel_ids),
                Message.published_at >= week_ago,
            )
            .group_by(Message.channel_id)
        )
        channel_7d = {row.channel_id: row.cnt for row in result_7d.all()}

    # Aggregate per collection
    stats: dict[str, dict] = {}
    for cid in accessible_ids:
        ch_ids = coll_channel_map[cid]
        total = sum(channel_total.get(ch, 0) for ch in ch_ids)
        last_24h = sum(channel_24h.get(ch, 0) for ch in ch_ids)
        last_7d = sum(channel_7d.get(ch, 0) for ch in ch_ids)

        stats[str(cid)] = {
            "collection_id": str(cid),
            "channel_count": len(ch_ids),
            "message_count": total,
            "message_count_24h": last_24h,
            "message_count_7d": last_7d,
        }

    return {"stats": stats}
