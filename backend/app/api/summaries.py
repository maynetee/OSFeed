import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.users import current_active_user
from app.database import get_db
from app.models.collection import Collection, collection_channels
from app.models.message import Message
from app.models.summary import Summary
from app.models.user import User
from app.schemas.summary import SummaryGenerateRequest, SummaryListResponse, SummaryResponse
from app.services.audit import record_audit_event
from app.services.summarization_service import generate_summary

logger = logging.getLogger(__name__)

router = APIRouter()

DATE_RANGE_MAP = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


@router.post("/generate", response_model=SummaryResponse)
async def generate_summary_endpoint(
    payload: SummaryGenerateRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an on-demand summary from messages in a collection or set of channels."""
    try:
        # Resolve channel IDs
        channel_ids: list[UUID] = []

        if payload.collection_id:
            result = await db.execute(
                select(Collection).where(Collection.id == payload.collection_id)
            )
            collection = result.scalar_one_or_none()
            if not collection:
                raise HTTPException(status_code=404, detail="Collection not found")
            if collection.user_id != user.id:
                raise HTTPException(status_code=403, detail="Not authorized")
            # Get channel IDs from collection_channels association table
            ch_result = await db.execute(
                select(collection_channels.c.channel_id).where(
                    collection_channels.c.collection_id == collection.id
                )
            )
            channel_ids = [row[0] for row in ch_result.all()]
        elif payload.channel_ids:
            channel_ids = payload.channel_ids
        else:
            raise HTTPException(status_code=400, detail="Provide collection_id or channel_ids")

        if not channel_ids:
            raise HTTPException(status_code=400, detail="No channels found for this scope")

        # Calculate date range
        delta = DATE_RANGE_MAP.get(payload.date_range)
        if not delta:
            raise HTTPException(status_code=400, detail="Invalid date_range. Use: 24h, 7d, 30d")

        date_end = datetime.now(timezone.utc)
        date_start = date_end - delta

        # Fetch messages
        query = (
            select(Message)
            .where(
                Message.channel_id.in_(channel_ids),
                Message.published_at >= date_start,
                Message.published_at <= date_end,
                Message.is_duplicate.is_(False),
            )
            .order_by(desc(Message.published_at))
            .limit(payload.max_messages)
        )
        result = await db.execute(query)
        db_messages = result.scalars().all()

        if not db_messages:
            raise HTTPException(status_code=400, detail="No messages found for the given scope and date range")

        # Format messages for LLM
        messages_for_llm = []
        for msg in db_messages:
            messages_for_llm.append({
                "original_text": msg.original_text or "",
                "translated_text": msg.translated_text or "",
                "published_at": msg.published_at.isoformat() if msg.published_at else "",
                "channel_title": "",
                "channel_username": "",
            })

        # Generate summary via LLM
        summary_result = await generate_summary(messages_for_llm)

        # Persist summary
        summary = Summary(
            user_id=user.id,
            collection_id=payload.collection_id,
            channel_ids=[str(cid) for cid in channel_ids],
            date_range_start=date_start,
            date_range_end=date_end,
            summary_text=summary_result["executive_summary"],
            key_themes=summary_result["key_themes"],
            notable_events=summary_result["notable_events"],
            message_count=len(db_messages),
            model_used=summary_result["model_used"],
            generation_time_seconds=summary_result["generation_time_seconds"],
        )
        db.add(summary)
        record_audit_event(
            db,
            user_id=user.id,
            action="summary.generate",
            resource_type="summary",
            resource_id=str(summary.id),
            metadata={
                "collection_id": str(payload.collection_id) if payload.collection_id else None,
                "message_count": len(db_messages),
                "date_range": payload.date_range,
            },
        )
        await db.commit()
        await db.refresh(summary)
        return summary

    except HTTPException:
        raise
    except (SQLAlchemyError, RuntimeError) as e:
        logger.error(f"Error generating summary for user {user.id}: {type(e).__name__}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="SUMMARY_GENERATION_ERROR")
    except Exception as e:
        logger.error(f"Unexpected error generating summary for user {user.id}: {type(e).__name__}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="SUMMARY_GENERATION_ERROR")


@router.get("", response_model=SummaryListResponse)
async def list_summaries(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List past summaries for the current user with pagination."""
    count_result = await db.execute(
        select(func.count()).select_from(Summary).where(Summary.user_id == user.id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Summary)
        .where(Summary.user_id == user.id)
        .order_by(desc(Summary.created_at))
        .offset(offset)
        .limit(limit)
    )
    summaries = result.scalars().all()
    return SummaryListResponse(summaries=summaries, total=total)


@router.get("/{summary_id}", response_model=SummaryResponse)
async def get_summary(
    summary_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific summary by ID."""
    result = await db.execute(select(Summary).where(Summary.id == summary_id))
    summary = result.scalar_one_or_none()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    if summary.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return summary


@router.delete("/{summary_id}")
async def delete_summary(
    summary_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a summary by ID."""
    result = await db.execute(select(Summary).where(Summary.id == summary_id))
    summary = result.scalar_one_or_none()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    if summary.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.delete(summary)
    record_audit_event(
        db,
        user_id=user.id,
        action="summary.delete",
        resource_type="summary",
        resource_id=str(summary_id),
    )
    await db.commit()
    return {"message": "Summary deleted"}
