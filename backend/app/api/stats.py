from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
import csv
from io import StringIO

from app.database import get_db
from app.models.message import Message
from app.models.channel import Channel
from app.models.summary import Summary
from app.models.user import User
from app.models.api_usage import ApiUsage
from app.auth.users import current_active_user

router = APIRouter()


@router.get("/overview")
async def get_overview_stats(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)

    total_messages = await db.execute(select(func.count()).select_from(Message))
    total_channels = await db.execute(select(func.count()).select_from(Channel).where(Channel.is_active == True))
    messages_24h = await db.execute(
        select(func.count()).select_from(Message).where(Message.published_at >= day_ago)
    )
    duplicates_24h = await db.execute(
        select(func.count()).select_from(Message)
        .where(Message.published_at >= day_ago)
        .where(Message.is_duplicate == True)
    )
    summaries_total = await db.execute(select(func.count()).select_from(Summary))

    return {
        "total_messages": total_messages.scalar() or 0,
        "active_channels": total_channels.scalar() or 0,
        "messages_last_24h": messages_24h.scalar() or 0,
        "duplicates_last_24h": duplicates_24h.scalar() or 0,
        "summaries_total": summaries_total.scalar() or 0,
    }


@router.get("/messages-by-day")
async def get_messages_by_day(
    days: int = Query(7, ge=1, le=90),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    start_date = datetime.utcnow() - timedelta(days=days)
    date_bucket = func.date(Message.published_at)

    result = await db.execute(
        select(date_bucket.label("day"), func.count().label("count"))
        .where(Message.published_at >= start_date)
        .group_by(date_bucket)
        .order_by(date_bucket)
    )
    rows = result.all()
    return [{"date": str(row.day), "count": row.count} for row in rows]


@router.get("/messages-by-channel")
async def get_messages_by_channel(
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Channel.id, Channel.title, func.count(Message.id).label("count"))
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
    filename = "telescope-stats.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/api-usage")
async def get_api_usage_stats(
    days: int = Query(7, ge=1, le=365),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    start_date = datetime.utcnow() - timedelta(days=days)

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
