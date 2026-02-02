from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update, or_, case
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timedelta
from io import BytesIO

import logging

from app.database import get_db
from app.models.collection import Collection, collection_channels
from app.models.collection_share import CollectionShare
from app.models.channel import Channel
from app.models.message import Message
from app.models.user import User
from app.schemas.collection import CollectionCreate, CollectionResponse, CollectionUpdate, CollectionStatsResponse
from app.schemas.collection_share import CollectionShareCreate, CollectionShareResponse
from app.auth.users import current_active_user
from app.services.audit import record_audit_event
from app.utils.response_cache import response_cache
from app.services.message_export_service import (
    export_messages_csv,
    export_messages_html,
    export_messages_pdf,
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def _load_channels(db: AsyncSession, channel_ids: List[UUID]) -> List[Channel]:
    if not channel_ids:
        return []
    result = await db.execute(select(Channel).where(Channel.id.in_(channel_ids)))
    channels = result.scalars().all()
    if len(channels) != len(set(channel_ids)):
        raise HTTPException(status_code=400, detail="One or more channels not found")
    return channels


async def _load_all_channels(db: AsyncSession) -> List[Channel]:
    result = await db.execute(select(Channel).where(Channel.is_active == True))
    return result.scalars().all()


async def _apply_default_collection(db: AsyncSession, user_id: UUID, collection: Collection):
    if collection.is_default:
        await db.execute(
            update(Collection)
            .where(Collection.user_id == user_id, Collection.id != collection.id)
            .values(is_default=False)
        )


async def _collection_channel_ids(db: AsyncSession, collection: Collection) -> List[UUID]:
    if collection.is_global:
        channels = await _load_all_channels(db)
        return [channel.id for channel in channels]
    return [channel.id for channel in collection.channels]


def _collection_response(collection: Collection, channel_ids: List[UUID]) -> CollectionResponse:
    return CollectionResponse(
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
    )


async def _get_collection_for_user(
    db: AsyncSession,
    collection_id: UUID,
    user_id: UUID,
) -> tuple[Collection, Optional[str]]:
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
    collection, permission = row
    if collection.user_id != user_id and not permission:
        raise HTTPException(status_code=403, detail="Not authorized to access this collection")
    return collection, permission


@router.get("", response_model=List[CollectionResponse])
async def list_collections(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
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

        responses.append(_collection_response(collection, channel_ids))

    return responses


@router.get("/overview")
@response_cache(expire=60, namespace="collections-overview")
async def get_collections_overview(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Step 1: Fetch user's collections (without loading full channel objects)
    result = await db.execute(
        select(Collection)
        .outerjoin(
            CollectionShare,
            (CollectionShare.collection_id == Collection.id) & (CollectionShare.user_id == user.id),
        )
        .where(or_(Collection.user_id == user.id, CollectionShare.user_id == user.id))
    )
    collections = result.scalars().all()
    
    if not collections:
        return {"collections": []}
    
    collection_ids = [c.id for c in collections]
    global_collection_ids = {c.id for c in collections if c.is_global}
    non_global_collection_ids = [c.id for c in collections if not c.is_global]
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    # Step 2: Get channel counts per non-global collection (single query on junction table)
    channel_counts: dict = {}
    if non_global_collection_ids:
        channel_count_result = await db.execute(
            select(
                collection_channels.c.collection_id,
                func.count(collection_channels.c.channel_id).label("channel_count")
            )
            .where(collection_channels.c.collection_id.in_(non_global_collection_ids))
            .group_by(collection_channels.c.collection_id)
        )
        channel_counts = {row.collection_id: row.channel_count for row in channel_count_result.all()}
    
    # Step 3: Get all active channel IDs and count for global collections
    all_active_channels_result = await db.execute(
        select(Channel.id).where(Channel.is_active == True)
    )
    all_active_channel_ids = [row[0] for row in all_active_channels_result.all()]
    global_channel_count = len(all_active_channel_ids)
    
    # Step 4: Build a mapping of collection_id -> list of channel_ids for message counting
    # For non-global collections, get channel IDs from junction table
    collection_channel_ids: dict = {c.id: [] for c in collections}
    
    if non_global_collection_ids:
        channel_ids_result = await db.execute(
            select(
                collection_channels.c.collection_id,
                collection_channels.c.channel_id
            )
            .where(collection_channels.c.collection_id.in_(non_global_collection_ids))
        )
        for row in channel_ids_result.all():
            collection_channel_ids[row.collection_id].append(row.channel_id)
    
    # For global collections, use all active channels
    for cid in global_collection_ids:
        collection_channel_ids[cid] = all_active_channel_ids
    
    # Step 5: Single grouped query for 7-day message counts
    # Build a union of (collection_id, channel_id) pairs for the query
    all_channel_ids_for_count = set()
    for cids in collection_channel_ids.values():
        all_channel_ids_for_count.update(cids)
    
    message_counts: dict = {c.id: 0 for c in collections}
    
    if all_channel_ids_for_count:
        # Get message counts grouped by channel_id
        channel_message_counts_result = await db.execute(
            select(
                Message.channel_id,
                func.count().label("msg_count")
            )
            .where(Message.channel_id.in_(list(all_channel_ids_for_count)))
            .where(Message.published_at >= week_ago)
            .group_by(Message.channel_id)
        )
        channel_msg_counts = {row.channel_id: row.msg_count for row in channel_message_counts_result.all()}
        
        # Aggregate message counts per collection
        for cid, chnl_ids in collection_channel_ids.items():
            message_counts[cid] = sum(channel_msg_counts.get(ch_id, 0) for ch_id in chnl_ids)
    
    # Step 6: Build the response
    overview = []
    for collection in collections:
        cid = collection.id
        if collection.is_global:
            ch_count = global_channel_count
        else:
            ch_count = channel_counts.get(cid, 0)
        
        overview.append({
            "id": str(cid),
            "name": collection.name,
            "message_count_7d": message_counts.get(cid, 0),
            "channel_count": ch_count,
            "created_at": collection.created_at,
        })
    
    return {"collections": overview}


@router.post("", response_model=CollectionResponse)
async def create_collection(
    payload: CollectionCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        channels = await _load_channels(db, payload.channel_ids or [])
        if payload.is_global:
            channels = []
        if payload.parent_id:
            await _get_collection_for_user(db, payload.parent_id, user.id)

        collection = Collection(
            user_id=user.id,
            name=payload.name,
            description=payload.description,
            color=payload.color,
            icon=payload.icon,
            is_default=payload.is_default,
            is_global=payload.is_global,
            parent_id=payload.parent_id,
            auto_assign_languages=payload.auto_assign_languages or [],
            auto_assign_keywords=payload.auto_assign_keywords or [],
            auto_assign_tags=payload.auto_assign_tags or [],
            channels=channels,
        )
        db.add(collection)
        await _apply_default_collection(db, user.id, collection)
        record_audit_event(
            db,
            user_id=user.id,
            action="collection.create",
            resource_type="collection",
            resource_id=str(collection.id),
            metadata={"channel_ids": [str(channel.id) for channel in channels]},
        )
        await db.commit()
        await db.refresh(collection)
        channel_ids = await _collection_channel_ids(db, collection)
        return _collection_response(collection, channel_ids)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating collection for user {user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create collection")


@router.get("/compare")
async def compare_collections(
    collection_ids: List[UUID] = Query(...),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Batch-load all requested collections with channels in a single query
    result = await db.execute(
        select(Collection, CollectionShare.permission)
        .options(selectinload(Collection.channels))
        .outerjoin(
            CollectionShare,
            (CollectionShare.collection_id == Collection.id) & (CollectionShare.user_id == user.id),
        )
        .where(Collection.id.in_(collection_ids))
    )
    rows = result.all()

    # Build lookup and verify access
    collections_map: dict[UUID, Collection] = {}
    for collection, permission in rows:
        if collection.user_id != user.id and not permission:
            raise HTTPException(status_code=403, detail="Not authorized to access this collection")
        collections_map[collection.id] = collection

    # Verify all requested collections were found
    for cid in collection_ids:
        if cid not in collections_map:
            raise HTTPException(status_code=404, detail="Collection not found")

    # Build per-collection channel_ids mapping
    all_active_channels: Optional[List[Channel]] = None
    collection_channel_map: dict[UUID, List[UUID]] = {}
    for cid, collection in collections_map.items():
        if collection.is_global:
            if all_active_channels is None:
                all_active_channels = await _load_all_channels(db)
            collection_channel_map[cid] = [ch.id for ch in all_active_channels]
        else:
            collection_channel_map[cid] = [ch.id for ch in collection.channels]

    # Gather all unique channel IDs for batch message counting
    all_channel_ids = set()
    for ch_ids in collection_channel_map.values():
        all_channel_ids.update(ch_ids)

    week_ago = datetime.utcnow() - timedelta(days=7)

    # Batch query: message counts and duplicate counts per channel
    channel_total_counts: dict[UUID, int] = {}
    channel_dup_counts: dict[UUID, int] = {}
    if all_channel_ids:
        total_result = await db.execute(
            select(Message.channel_id, func.count().label("cnt"))
            .where(Message.channel_id.in_(list(all_channel_ids)))
            .where(Message.published_at >= week_ago)
            .group_by(Message.channel_id)
        )
        for row in total_result.all():
            channel_total_counts[row.channel_id] = row.cnt

        dup_result = await db.execute(
            select(Message.channel_id, func.count().label("cnt"))
            .where(Message.channel_id.in_(list(all_channel_ids)))
            .where(Message.published_at >= week_ago)
            .where(Message.is_duplicate == True)
            .group_by(Message.channel_id)
        )
        for row in dup_result.all():
            channel_dup_counts[row.channel_id] = row.cnt

    # Build results preserving requested order
    results = []
    for cid in collection_ids:
        collection = collections_map[cid]
        ch_ids = collection_channel_map[cid]
        total = sum(channel_total_counts.get(ch_id, 0) for ch_id in ch_ids)
        duplicates = sum(channel_dup_counts.get(ch_id, 0) for ch_id in ch_ids)
        results.append(
            {
                "collection_id": str(collection.id),
                "name": collection.name,
                "message_count_7d": total,
                "channel_count": len(ch_ids),
                "duplicate_rate": round(duplicates / total, 3) if total else 0.0,
            }
        )

    return {"comparisons": results}


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, _ = await _get_collection_for_user(db, collection_id, user.id)
    await db.refresh(collection, attribute_names=["channels"])
    channel_ids = await _collection_channel_ids(db, collection)
    return _collection_response(collection, channel_ids)


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: UUID,
    payload: CollectionUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, permission = await _get_collection_for_user(db, collection_id, user.id)
    if collection.user_id != user.id and permission not in {"editor", "admin"}:
        raise HTTPException(status_code=403, detail="Not authorized to update this collection")
    if collection.user_id != user.id:
        restricted_fields = [
            payload.is_default,
            payload.is_global,
            payload.parent_id,
            payload.auto_assign_languages,
            payload.auto_assign_keywords,
            payload.auto_assign_tags,
        ]
        if any(field is not None for field in restricted_fields):
            raise HTTPException(status_code=403, detail="Not authorized to change collection settings")
    await db.refresh(collection, attribute_names=["channels"])

    if payload.name is not None:
        collection.name = payload.name
    if payload.description is not None:
        collection.description = payload.description
    if payload.color is not None:
        collection.color = payload.color
    if payload.icon is not None:
        collection.icon = payload.icon
    if payload.is_default is not None:
        collection.is_default = payload.is_default
    if payload.is_global is not None:
        collection.is_global = payload.is_global
        if payload.is_global:
            collection.channels = []
    if payload.parent_id is not None:
        if payload.parent_id:
            await _get_collection_for_user(db, payload.parent_id, user.id)
        collection.parent_id = payload.parent_id
    if payload.auto_assign_languages is not None:
        collection.auto_assign_languages = payload.auto_assign_languages
    if payload.auto_assign_keywords is not None:
        collection.auto_assign_keywords = payload.auto_assign_keywords
    if payload.auto_assign_tags is not None:
        collection.auto_assign_tags = payload.auto_assign_tags
    if payload.channel_ids is not None:
        collection.channels = await _load_channels(db, payload.channel_ids)

    await _apply_default_collection(db, user.id, collection)
    record_audit_event(
        db,
        user_id=user.id,
        action="collection.update",
        resource_type="collection",
        resource_id=str(collection.id),
        metadata={"channel_ids": [str(channel.id) for channel in collection.channels]},
    )
    await db.commit()
    await db.refresh(collection)
    channel_ids = await _collection_channel_ids(db, collection)
    return _collection_response(collection, channel_ids)


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, permission = await _get_collection_for_user(db, collection_id, user.id)
    if collection.user_id != user.id and permission != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this collection")

    await db.delete(collection)
    record_audit_event(
        db,
        user_id=user.id,
        action="collection.delete",
        resource_type="collection",
        resource_id=str(collection.id),
    )
    await db.commit()

    return {"message": "Collection deleted successfully"}


@router.get("/{collection_id}/stats", response_model=CollectionStatsResponse)
@response_cache(expire=60, namespace="collection-stats")
async def get_collection_stats(
    collection_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, _ = await _get_collection_for_user(db, collection_id, user.id)
    await db.refresh(collection, attribute_names=["channels"])
    channel_ids = await _collection_channel_ids(db, collection)
    if not channel_ids:
        return CollectionStatsResponse(
            message_count=0,
            message_count_24h=0,
            message_count_7d=0,
            channel_count=0,
            top_channels=[],
            activity_trend=[],
            duplicate_rate=0.0,
            languages={},
        )

    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    # Query 1: Combined grouped query for counts, activity trend, and languages
    # Group by (day, source_language) to derive all stats in a single pass
    date_bucket = func.date(Message.published_at)
    stats_result = await db.execute(
        select(
            date_bucket.label("day"),
            Message.source_language,
            func.count().label("count"),
            func.sum(case((Message.is_duplicate == True, 1), else_=0)).label("dup_count"),
        )
        .where(Message.channel_id.in_(channel_ids))
        .group_by(date_bucket, Message.source_language)
    )
    stats_rows = stats_result.all()

    # Derive all metrics from the grouped result in Python
    total = 0
    duplicates = 0
    count_24h = 0
    count_7d = 0
    activity_by_day: dict = {}
    languages: dict = {}

    for row in stats_rows:
        total += row.count
        duplicates += row.dup_count

        if row.day is not None:
            row_date = row.day if isinstance(row.day, datetime) else datetime.combine(row.day, datetime.min.time())
            if row_date >= day_ago:
                count_24h += row.count
            if row_date >= week_ago:
                count_7d += row.count
                # Activity trend: aggregate by day for last 7 days
                day_str = str(row.day)
                activity_by_day[day_str] = activity_by_day.get(day_str, 0) + row.count
                # Languages: aggregate by language for last 7 days
                if row.source_language:
                    languages[row.source_language] = languages.get(row.source_language, 0) + row.count

    activity_trend = [
        {"date": day, "count": count}
        for day, count in sorted(activity_by_day.items())
    ]

    duplicate_rate = round(duplicates / total, 3) if total else 0.0

    # Query 2: Top channels by message count
    top_channels_result = await db.execute(
        select(Channel.id, Channel.title, func.count(Message.id).label("count"))
        .join(Message, Message.channel_id == Channel.id)
        .where(Message.channel_id.in_(channel_ids))
        .group_by(Channel.id, Channel.title)
        .order_by(desc("count"))
        .limit(5)
    )
    top_channels = [
        {"channel_id": str(row.id), "channel_title": row.title, "count": row.count}
        for row in top_channels_result.all()
    ]

    return CollectionStatsResponse(
        message_count=total,
        message_count_24h=count_24h,
        message_count_7d=count_7d,
        channel_count=len(channel_ids),
        top_channels=top_channels,
        activity_trend=activity_trend,
        duplicate_rate=duplicate_rate,
        languages=languages,
    )


@router.post("/{collection_id}/export")
async def export_collection_messages(
    collection_id: UUID,
    format: str = "csv",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(200, ge=1, le=1000),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, _ = await _get_collection_for_user(db, collection_id, user.id)
    await db.refresh(collection, attribute_names=["channels"])
    channel_ids = await _collection_channel_ids(db, collection)
    if not channel_ids:
        raise HTTPException(status_code=400, detail="Collection has no channels")

    if format == "csv":
        filename = f"osfeed-collection-{collection_id}.csv"
        return StreamingResponse(
            export_messages_csv(
                user_id=user.id,
                channel_ids=channel_ids,
                start_date=start_date,
                end_date=end_date,
            ),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    if format == "html":
        filename = f"osfeed-collection-{collection_id}.html"
        return StreamingResponse(
            export_messages_html(
                user_id=user.id,
                channel_ids=channel_ids,
                start_date=start_date,
                end_date=end_date,
            ),
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    if format == "pdf":
        filename = f"osfeed-collection-{collection_id}.pdf"
        pdf_bytes = await export_messages_pdf(
            user_id=user.id,
            channel_ids=channel_ids,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )

    raise HTTPException(status_code=400, detail="Unsupported export format")


@router.get("/{collection_id}/shares", response_model=List[CollectionShareResponse])
async def list_collection_shares(
    collection_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, _ = await _get_collection_for_user(db, collection_id, user.id)
    if collection.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view shares")
    result = await db.execute(select(CollectionShare).where(CollectionShare.collection_id == collection_id))
    return result.scalars().all()


@router.post("/{collection_id}/shares", response_model=CollectionShareResponse)
async def add_collection_share(
    collection_id: UUID,
    payload: CollectionShareCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, _ = await _get_collection_for_user(db, collection_id, user.id)
    if collection.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to share this collection")
    result = await db.execute(
        select(CollectionShare)
        .where(CollectionShare.collection_id == collection_id)
        .where(CollectionShare.user_id == payload.user_id)
    )
    share = result.scalar_one_or_none()
    if share:
        share.permission = payload.permission
    else:
        share = CollectionShare(
            collection_id=collection_id,
            user_id=payload.user_id,
            permission=payload.permission,
        )
        db.add(share)
    await db.commit()
    await db.refresh(share)
    return share


@router.delete("/{collection_id}/shares/{share_user_id}")
async def delete_collection_share(
    collection_id: UUID,
    share_user_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, _ = await _get_collection_for_user(db, collection_id, user.id)
    if collection.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to remove shares")
    result = await db.execute(
        select(CollectionShare)
        .where(CollectionShare.collection_id == collection_id)
        .where(CollectionShare.user_id == share_user_id)
    )
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    await db.delete(share)
    await db.commit()
    return {"message": "Share removed"}
