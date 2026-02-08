import logging
from datetime import datetime, timedelta
from io import BytesIO
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import case, desc, func, or_, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.users import current_active_user
from app.database import get_db
from app.models.channel import Channel, user_channels
from app.models.collection import Collection, collection_channels
from app.models.collection_share import CollectionShare
from app.models.message import Message
from app.models.user import User
from app.schemas.collection import (
    CollectionCreate,
    CollectionResponse,
    CollectionStatsResponse,
    CollectionUpdate,
    CuratedCollectionResponse,
)
from app.schemas.collection_share import CollectionShareCreate, CollectionShareResponse
from app.services.audit import record_audit_event
from app.services.message_export_service import (
    export_messages_csv,
    export_messages_html,
    export_messages_pdf,
)
from app.utils.response_cache import response_cache

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
        is_curated=collection.is_curated,
        region=collection.region,
        topic=collection.topic,
        curator=collection.curator,
        thumbnail_url=collection.thumbnail_url,
        last_curated_at=collection.last_curated_at,
        curated_channel_usernames=collection.curated_channel_usernames,
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
    """Get all collections owned by or shared with the current user.

    Returns a list of collections including both personal and shared collections.
    For global collections, automatically includes all active channels. For regular
    collections, includes only assigned channels. Efficiently loads channel data
    using eager loading for optimal performance.

    Returns:
        List[CollectionResponse]: List of collections with their channels and settings.
    """
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
    """Get a summary overview of all collections with message counts and channel counts.

    Provides a lightweight overview for dashboard displays and collection lists.
    Returns message counts from the last 7 days and total channel counts for each
    collection. Uses optimized queries to minimize database load and includes
    60-second response caching for improved performance.

    Returns:
        dict: Overview with collections array containing id, name, message_count_7d,
              channel_count, and created_at for each collection.
    """
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
    """Create a new collection with specified channels and settings.

    Allows users to create custom collections for organizing RSS feed channels.
    Supports global collections (all active channels), default collection flag,
    parent-child relationships, and auto-assignment rules based on languages,
    keywords, or tags. Records audit trail for creation event.

    Args:
        payload: Collection creation data including name, channels, and settings.

    Returns:
        CollectionResponse: The newly created collection with all properties.

    Raises:
        HTTPException: 400 if channels not found, 404 if parent not found,
                      500 for database or unexpected errors.
    """
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
    except (SQLAlchemyError, IntegrityError) as e:
        logger.error(f"Database error creating collection for user {user.id}: {type(e).__name__}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="COLLECTION_CREATE_DATABASE_ERROR")
    except Exception as e:
        logger.error(f"Unexpected error creating collection for user {user.id}: {type(e).__name__}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="COLLECTION_CREATE_ERROR")


@router.get("/curated", response_model=List[CuratedCollectionResponse])
async def list_curated_collections(
    region: Optional[str] = None,
    topic: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all curated collections. Public endpoint, no auth required."""
    query = select(Collection).where(Collection.is_curated == True)
    if region:
        query = query.where(Collection.region == region)
    if topic:
        query = query.where(Collection.topic == topic)
    if search:
        query = query.where(
            or_(
                Collection.name.ilike(f"%{search}%"),
                Collection.description.ilike(f"%{search}%"),
            )
        )
    result = await db.execute(query.order_by(Collection.name))
    collections = result.scalars().all()
    return [
        CuratedCollectionResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            region=c.region,
            topic=c.topic,
            curator=c.curator,
            channel_count=len(c.curated_channel_usernames or []),
            curated_channel_usernames=c.curated_channel_usernames or [],
            thumbnail_url=c.thumbnail_url,
            last_curated_at=c.last_curated_at,
        )
        for c in collections
    ]


@router.get("/curated/{collection_id}", response_model=CuratedCollectionResponse)
async def get_curated_collection(
    collection_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific curated collection by ID. Public endpoint, no auth required."""
    result = await db.execute(
        select(Collection).where(Collection.id == collection_id, Collection.is_curated == True)
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=404, detail="Curated collection not found")
    return CuratedCollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        region=collection.region,
        topic=collection.topic,
        curator=collection.curator,
        channel_count=len(collection.curated_channel_usernames or []),
        curated_channel_usernames=collection.curated_channel_usernames or [],
        thumbnail_url=collection.thumbnail_url,
        last_curated_at=collection.last_curated_at,
    )


@router.post("/curated/{collection_id}/import")
async def import_curated_collection(
    collection_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Import all channels from a curated collection to user's sources."""
    result = await db.execute(
        select(Collection).where(Collection.id == collection_id, Collection.is_curated == True)
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=404, detail="Curated collection not found")

    usernames = collection.curated_channel_usernames or []
    if not usernames:
        return {"imported_count": 0, "already_existed": 0}

    # Batch-load all existing channels by username in one query
    ch_result = await db.execute(
        select(Channel).where(Channel.username.in_(usernames))
    )
    existing_channels = {ch.username: ch for ch in ch_result.scalars().all()}

    # Create missing channels in bulk
    for username in usernames:
        if username not in existing_channels:
            channel = Channel(
                username=username,
                title=username,
                is_active=False,
            )
            db.add(channel)
            existing_channels[username] = channel
    await db.flush()

    # Batch-load existing user-channel links
    all_channel_ids = [ch.id for ch in existing_channels.values()]
    link_result = await db.execute(
        select(user_channels.c.channel_id).where(
            user_channels.c.user_id == user.id,
            user_channels.c.channel_id.in_(all_channel_ids),
        )
    )
    already_linked_ids = {row.channel_id for row in link_result.all()}

    imported_count = 0
    already_existed = 0

    for username in usernames:
        channel = existing_channels[username]
        if channel.id in already_linked_ids:
            already_existed += 1
            continue

        await db.execute(
            user_channels.insert().values(
                user_id=user.id,
                channel_id=channel.id,
            )
        )
        imported_count += 1

    return {"imported_count": imported_count, "already_existed": already_existed}


@router.get("/compare")
@response_cache(expire=60, namespace="collections-compare")
async def compare_collections(
    collection_ids: List[UUID] = Query(...),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Compare message counts and duplicate rates across multiple collections.

    Performs side-by-side comparison of multiple collections to help users analyze
    collection performance and content overlap. Returns metrics from the last 7 days
    including total message counts, channel counts, and duplicate detection rates.
    Uses batch queries for optimal performance with 60-second response caching.

    Args:
        collection_ids: List of collection UUIDs to compare.

    Returns:
        dict: Comparisons array with collection_id, name, message_count_7d,
              channel_count, and duplicate_rate for each collection.

    Raises:
        HTTPException: 403 if not authorized to access a collection,
                      404 if any collection not found.
    """
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
    """Get a specific collection by ID with full details.

    Retrieves complete collection information including name, description, settings,
    and associated channels. Verifies user has access either as owner or through
    shared permissions. For global collections, automatically includes all active channels.

    Args:
        collection_id: UUID of the collection to retrieve.

    Returns:
        CollectionResponse: Complete collection details with channels and settings.

    Raises:
        HTTPException: 403 if not authorized, 404 if collection not found.
    """
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
    """Update a collection's name, channels, settings, or other properties.

    Allows modification of collection properties including name, description, visual
    settings (color, icon), channel assignments, and automation rules. Enforces
    permission-based restrictions: owners can modify all fields, while editor/admin
    shared users can only update name, description, channels, color, and icon.
    Records audit trail for updates.

    Args:
        collection_id: UUID of the collection to update.
        payload: Collection update data with optional fields.

    Returns:
        CollectionResponse: Updated collection with all current properties.

    Raises:
        HTTPException: 403 if not authorized or attempting to change restricted fields,
                      404 if collection or parent not found, 400 if channels not found.
    """
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
    """Delete a collection permanently and remove all sharing permissions.

    Permanently removes a collection from the database. Only collection owners or
    users with admin shared permission can delete collections. This operation also
    cascades to remove all associated sharing permissions. Records audit trail
    for deletion event.

    Args:
        collection_id: UUID of the collection to delete.

    Returns:
        dict: Success message confirming deletion.

    Raises:
        HTTPException: 403 if not authorized to delete, 404 if collection not found.
    """
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
    """Get detailed statistics for a collection including message counts, activity trends, and top channels.

    Provides comprehensive analytics for collection monitoring and analysis. Returns
    all-time and time-bounded metrics (24h, 7d), daily activity trends, language
    distribution, duplicate detection rates, and top 5 most active channels.
    Uses optimized queries with efficient indexing and includes 60-second response
    caching for improved performance.

    Args:
        collection_id: UUID of the collection to analyze.

    Returns:
        CollectionStatsResponse: Complete statistics including message_count,
                                message_count_24h, message_count_7d, channel_count,
                                top_channels, activity_trend, duplicate_rate, and languages.

    Raises:
        HTTPException: 403 if not authorized, 404 if collection not found.
    """
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

    # Query 1: All-time aggregation for total count and duplicate count
    all_time_result = await db.execute(
        select(
            func.count().label("total"),
            func.sum(case((Message.is_duplicate == True, 1), else_=0)).label("duplicates"),
        )
        .where(Message.channel_id.in_(channel_ids))
    )
    all_time_row = all_time_result.first()
    total = all_time_row.total if all_time_row else 0
    duplicates = all_time_row.duplicates if all_time_row else 0

    # Query 2: Time-bounded grouped query for recent metrics (last 7 days)
    # This WHERE clause enables efficient use of ix_messages_channel_published_lang index
    date_bucket = func.date(Message.published_at)
    recent_stats_result = await db.execute(
        select(
            date_bucket.label("day"),
            Message.source_language,
            func.count().label("count"),
        )
        .where(Message.channel_id.in_(channel_ids))
        .where(Message.published_at >= week_ago)
        .group_by(date_bucket, Message.source_language)
    )
    recent_stats_rows = recent_stats_result.all()

    # Derive recent metrics from the grouped result in Python
    count_24h = 0
    count_7d = 0
    activity_by_day: dict = {}
    languages: dict = {}

    for row in recent_stats_rows:
        count_7d += row.count

        if row.day is not None:
            row_date = row.day if isinstance(row.day, datetime) else datetime.combine(row.day, datetime.min.time())
            if row_date >= day_ago:
                count_24h += row.count

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
    limit: int = Query(200, ge=1, le=200),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Export collection messages in CSV, HTML, or PDF format with optional date filtering.

    Generates downloadable exports of collection messages for archival, reporting,
    or external analysis. Supports three formats: CSV for data analysis, HTML for
    readable web viewing, and PDF for professional reports. Allows filtering by
    date range and includes configurable message limits (1-1000, default 200 for PDF).

    Args:
        collection_id: UUID of the collection to export.
        format: Export format - "csv", "html", or "pdf" (default: "csv").
        start_date: Optional start date for filtering messages.
        end_date: Optional end date for filtering messages.
        limit: Maximum number of messages to include (default: 200, max: 1000).

    Returns:
        StreamingResponse: File download with appropriate content-type and filename.

    Raises:
        HTTPException: 400 if collection has no channels or format unsupported,
                      403 if not authorized, 404 if collection not found.
    """
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
    """Get all sharing permissions for a collection.

    Retrieves the list of users who have been granted access to a collection
    along with their permission levels (viewer, editor, or admin). Only the
    collection owner can view the sharing list to maintain privacy and security.

    Args:
        collection_id: UUID of the collection to query.

    Returns:
        List[CollectionShareResponse]: List of sharing permissions with user_id and permission level.

    Raises:
        HTTPException: 403 if not the collection owner, 404 if collection not found.
    """
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
    """Share a collection with another user or update their permission level.

    Grants access to a collection for collaborative viewing, editing, or administration.
    Permission levels include: viewer (read-only), editor (can modify content and
    channels), and admin (can delete and manage sharing). If the user already has
    access, updates their permission level. Only the collection owner can manage shares.

    Args:
        collection_id: UUID of the collection to share.
        payload: Sharing data including user_id and permission level.

    Returns:
        CollectionShareResponse: The created or updated sharing permission.

    Raises:
        HTTPException: 403 if not the collection owner, 404 if collection not found.
    """
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
    """Remove a user's access to a shared collection.

    Revokes all access permissions for a specific user, removing their ability to
    view or interact with the collection. This operation cannot be undone - the user
    must be re-invited to regain access. Only the collection owner can remove shares.

    Args:
        collection_id: UUID of the collection.
        share_user_id: UUID of the user whose access should be removed.

    Returns:
        dict: Success message confirming share removal.

    Raises:
        HTTPException: 403 if not the collection owner, 404 if collection or share not found.
    """
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
