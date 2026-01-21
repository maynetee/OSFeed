from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List

from app.database import get_db
from app.models.narrative_cluster import NarrativeCluster
from app.models.entity import Entity, message_entity_association
from app.models.message import Message
from app.schemas.intelligence import IntelligenceDashboard, ClusterList, ClusterDetail, EntityRef

router = APIRouter()

@router.get("/dashboard", response_model=IntelligenceDashboard)
async def get_intelligence_dashboard(db: AsyncSession = Depends(get_db)):
    stmt = select(NarrativeCluster).order_by(
        desc(NarrativeCluster.urgency_score),
        desc(NarrativeCluster.updated_at)
    ).limit(5)
    result = await db.execute(stmt)
    hot_topics = result.scalars().all()
    
    entities_map = {"ORG": [], "LOC": [], "PER": []}
    for type_ in entities_map.keys():
        stmt = select(Entity).where(Entity.type == type_).order_by(desc(Entity.frequency)).limit(10)
        res = await db.execute(stmt)
        entities_map[type_] = [
            EntityRef(id=e.id, name=e.name, type=e.type, frequency=e.frequency) 
            for e in res.scalars().all()
        ]
        
    return IntelligenceDashboard(
        hot_topics=[ClusterList.model_validate(c) for c in hot_topics],
        top_entities=entities_map,
        global_tension=sum(c.urgency_score or 0 for c in hot_topics) // max(1, len(hot_topics))
    )

@router.get("/clusters/{cluster_id}", response_model=ClusterDetail)
async def get_cluster_detail(cluster_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(NarrativeCluster).where(NarrativeCluster.id == cluster_id)
    result = await db.execute(stmt)
    cluster = result.scalar_one_or_none()
    
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
        
    msg_stmt = select(Message).where(Message.cluster_id == cluster_id).order_by(desc(Message.novelty_score)).limit(5)
    msg_result = await db.execute(msg_stmt)
    messages = msg_result.scalars().all()
    
    entity_stmt = select(Entity).join(
        message_entity_association, Entity.id == message_entity_association.c.entity_id
    ).join(
        Message, Message.id == message_entity_association.c.message_id
    ).where(
        Message.cluster_id == cluster_id
    ).group_by(Entity.id).order_by(desc(func.count(Message.id))).limit(20)
    
    entity_result = await db.execute(entity_stmt)
    entities = entity_result.scalars().all()
    
    return ClusterDetail(
        **cluster.__dict__,
        messages_preview=[{"id": m.id, "text": m.translated_text or m.original_text} for m in messages],
        entities=[EntityRef(id=e.id, name=e.name, type=e.type, frequency=e.frequency) for e in entities],
        timeline=[] 
    )
