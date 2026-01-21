from typing import List, Optional, Tuple
from uuid import UUID
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.narrative_cluster import NarrativeCluster
from app.services.vector_store import vector_store
from app.services.summary_generator import StructuredSummaryService

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.85
NOVELTY_THRESHOLD = 0.75

class ClusteringService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.summarizer = StructuredSummaryService()

    async def process_single_message(self, message: Message) -> bool:
        text = message.translated_text or message.original_text or ""
        
        # 1. Cost Optimization Filter: Ignore short noise
        if len(text) < 50:
            return False

        # 2. Embed if needed (VectorStore handles idempotency roughly, but let's be explicit)
        if not message.embedding_id:
             # This will trigger OpenAI call via VectorStore -> Embedder
             # vector_store.add_documents handles embedding generation
             # But here we are inside clustering, we need the vector
             pass
        
        # Actually, let's use a helper that ensures embedding exists
        # We need the vector to calculate novelty and find cluster
        try:
            vector = await vector_store.get_or_create_embedding(text, str(message.id))
            if not vector:
                return False
                
            # Update DB with embedding_id if not present (optimization)
            if not message.embedding_id:
                message.embedding_id = str(message.id) # Depending on how vector_store assigns IDs
                
            # 3. Calculate Intelligence
            novelty = await self._calculate_novelty(message)
            message.novelty_score = int(novelty * 100)
            
            urgency = self._calculate_urgency(message)
            
            cluster_id = await self._find_matching_cluster(message)
            
            if cluster_id:
                message.cluster_id = cluster_id
                await self._update_cluster_stats(cluster_id, message, urgency)
            else:
                new_cluster = NarrativeCluster(
                    message_count=1,
                    title=f"New Topic {datetime.now().strftime('%H:%M')}",
                    urgency_score=urgency,
                    first_message_at=message.published_at,
                    last_message_at=message.published_at,
                    primary_source_channel_id=message.channel_id
                )
                self.session.add(new_cluster)
                await self.session.flush()
                message.cluster_id = new_cluster.id
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to process single message for clustering: {e}")
            return False

    async def process_unclustered_messages(self, hours_lookback: int = 24, batch_size: int = 50):
        # 1. Fetch unclustered messages with embeddings
        lookback_time = datetime.now(timezone.utc) - timedelta(hours=hours_lookback)
        
        stmt = select(Message).where(
            and_(
                Message.cluster_id.is_(None),
                Message.embedding_id.isnot(None),
                Message.published_at >= lookback_time
            )
        ).limit(batch_size)
        
        result = await self.session.execute(stmt)
        messages = result.scalars().all()
        
        if not messages:
            return 0

        count_clustered = 0
        
        for message in messages:
            novelty = await self._calculate_novelty(message)
            message.novelty_score = int(novelty * 100)
            
            urgency = self._calculate_urgency(message)

            cluster_id = await self._find_matching_cluster(message)
            
            if cluster_id:
                message.cluster_id = cluster_id
                await self._update_cluster_stats(cluster_id, message, urgency)
            else:
                new_cluster = NarrativeCluster(
                    message_count=1,
                    title=f"New Topic {datetime.now().strftime('%H:%M')}",
                    urgency_score=urgency,
                    first_message_at=message.published_at,
                    last_message_at=message.published_at,
                    primary_source_channel_id=message.channel_id
                )
                self.session.add(new_cluster)
                await self.session.flush()
                message.cluster_id = new_cluster.id
            
            count_clustered += 1

        await self.session.commit()
        return count_clustered

    async def _update_cluster_stats(self, cluster_id: UUID, message: Message, urgency: int):
        stmt = select(NarrativeCluster).where(NarrativeCluster.id == cluster_id)
        result = await self.session.execute(stmt)
        cluster = result.scalar_one_or_none()
        
        if not cluster:
            return

        cluster.message_count += 1
        cluster.updated_at = datetime.now(timezone.utc)
        
        if urgency > 5:
            cluster.urgency_score = (cluster.urgency_score or 0) + 1
            
        if not cluster.first_message_at or (message.published_at and message.published_at < cluster.first_message_at):
            cluster.first_message_at = message.published_at
            cluster.primary_source_channel_id = message.channel_id
            
        if not cluster.last_message_at or (message.published_at and message.published_at > cluster.last_message_at):
            cluster.last_message_at = message.published_at

        if cluster.first_message_at:
            age_hours = (datetime.now(timezone.utc) - cluster.first_message_at).total_seconds() / 3600
            cluster.velocity = cluster.message_count / max(0.1, age_hours)
            
        cluster.emergence_score = (cluster.velocity or 0) * (1 + (cluster.urgency_score or 0) / 10)

        # Trigger Summary Generation (Feature #7)
        # Conditions: Significant size (5+) and update interval (every 10 messages)
        # Or High Urgency jump (TODO: track urgency delta, but simplistic approach here)
        if cluster.message_count >= 5 and cluster.message_count % 10 == 0:
            try:
                # Fetch recent messages for context
                # Need to use a new session or current session to fetch messages text
                # We can't use relationships easily in async without explicit loading sometimes
                # Let's run a select
                msg_stmt = select(Message.translated_text, Message.original_text)\
                    .where(Message.cluster_id == cluster_id)\
                    .order_by(Message.published_at.desc())\
                    .limit(20)
                msg_result = await self.session.execute(msg_stmt)
                texts = [row.translated_text or row.original_text for row in msg_result.all()]
                
                summary = await self.summarizer.generate_summary(texts)
                if summary:
                    cluster.structured_summary = summary
                    cluster.title = summary.get("headline", cluster.title)
                    cluster.summary = summary.get("context", cluster.summary)
            except Exception as e:
                logger.error(f"Failed to generate summary for cluster {cluster_id}: {e}")

    def _calculate_urgency(self, message: Message) -> int:
        text = (message.translated_text or message.original_text or "").lower()
        score = 0
        
        keywords = [
            "attack", "strike", "bomb", "explosion", "casualty", "dead", "killed", 
            "war", "invasion", "emergency", "alert", "breaking", "urgent",
            "nuclear", "missile", "drone", "assassination"
        ]
        
        for k in keywords:
            if k in text:
                score += 2 if k in ["breaking", "urgent", "nuclear"] else 1
                
        return min(10, score)

    async def _calculate_novelty(self, message: Message) -> float:
        matches = await vector_store.query_similar(
            text=message.translated_text or message.original_text or "",
            top_k=1
        )
        
        if not matches:
            return 1.0
            
        best_score = 0.0
        for match in matches:
            if str(match['id']) != str(message.embedding_id):
                 best_score = max(best_score, match['score'])
        
        return max(0.0, 1.0 - best_score)

    async def _find_matching_cluster(self, message: Message) -> Optional[UUID]:
        matches = await vector_store.query_similar(
            text=message.translated_text or message.original_text or "",
            top_k=5
        )
        
        if not matches:
            return None
            
        vector_ids = [m['id'] for m in matches if m['score'] >= SIMILARITY_THRESHOLD]
        if not vector_ids:
            return None
            
        stmt = select(Message.cluster_id).where(
            and_(
                Message.embedding_id.in_(vector_ids),
                Message.cluster_id.isnot(None)
            )
        )
        result = await self.session.execute(stmt)
        existing_cluster_ids = result.scalars().all()
        
        if existing_cluster_ids:
            from collections import Counter
            return Counter(existing_cluster_ids).most_common(1)[0][0]
            
        return None
