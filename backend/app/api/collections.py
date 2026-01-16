from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List

from app.database import get_db
from app.models.collection import Collection
from app.models.channel import Channel
from app.models.user import User
from app.schemas.collection import CollectionCreate, CollectionResponse, CollectionUpdate
from app.auth.users import current_active_user
from app.services.audit import record_audit_event

router = APIRouter()


async def _load_channels(db: AsyncSession, channel_ids: List[UUID]) -> List[Channel]:
    if not channel_ids:
        return []
    result = await db.execute(select(Channel).where(Channel.id.in_(channel_ids)))
    channels = result.scalars().all()
    if len(channels) != len(set(channel_ids)):
        raise HTTPException(status_code=400, detail="One or more channels not found")
    return channels


@router.get("", response_model=List[CollectionResponse])
async def list_collections(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Collection)
        .options(selectinload(Collection.channels))
        .where(Collection.user_id == user.id)
    )
    collections = result.scalars().all()
    return [
        CollectionResponse(
            id=collection.id,
            user_id=collection.user_id,
            name=collection.name,
            description=collection.description,
            channel_ids=[channel.id for channel in collection.channels],
            created_at=collection.created_at,
            updated_at=collection.updated_at,
        )
        for collection in collections
    ]


@router.post("", response_model=CollectionResponse)
async def create_collection(
    payload: CollectionCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    channels = await _load_channels(db, payload.channel_ids or [])

    collection = Collection(
        user_id=user.id,
        name=payload.name,
        description=payload.description,
        channels=channels,
    )
    db.add(collection)
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

    return CollectionResponse(
        id=collection.id,
        user_id=collection.user_id,
        name=collection.name,
        description=collection.description,
        channel_ids=[channel.id for channel in collection.channels],
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Collection)
        .options(selectinload(Collection.channels))
        .where(Collection.id == collection_id, Collection.user_id == user.id)
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    return CollectionResponse(
        id=collection.id,
        user_id=collection.user_id,
        name=collection.name,
        description=collection.description,
        channel_ids=[channel.id for channel in collection.channels],
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: UUID,
    payload: CollectionUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Collection)
        .options(selectinload(Collection.channels))
        .where(Collection.id == collection_id, Collection.user_id == user.id)
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if payload.name is not None:
        collection.name = payload.name
    if payload.description is not None:
        collection.description = payload.description
    if payload.channel_ids is not None:
        collection.channels = await _load_channels(db, payload.channel_ids)

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

    return CollectionResponse(
        id=collection.id,
        user_id=collection.user_id,
        name=collection.name,
        description=collection.description,
        channel_ids=[channel.id for channel in collection.channels],
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Collection).where(Collection.id == collection_id, Collection.user_id == user.id)
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

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
