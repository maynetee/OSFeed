import logging
from app.database import AsyncSessionLocal
from app.services.clustering import ClusteringService

logger = logging.getLogger(__name__)

async def run_clustering_job():
    async with AsyncSessionLocal() as session:
        try:
            service = ClusteringService(session)
            count = await service.process_unclustered_messages()
            if count > 0:
                logger.info(f"Clustered {count} new messages")
        except Exception as e:
            logger.error(f"Clustering job failed: {e}", exc_info=True)
