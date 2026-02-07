from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.users import current_active_user
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.insights import InsightsDashboardResponse
from app.services.insights_service import insights_service
from app.utils.response_cache import response_cache

router = APIRouter()
settings = get_settings()


@router.get("/dashboard", response_model=InsightsDashboardResponse)
@response_cache(expire=60, namespace="insights-dashboard")
async def get_insights_dashboard(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI intelligence insights for the dashboard.

    Returns signal counts, AI-generated intelligence tips, trending topics,
    and activity spike detection for the authenticated user's channels.
    """
    import asyncio

    signals, tips, topics, spikes = await asyncio.gather(
        insights_service.get_signals_processed(user.id, db),
        insights_service.generate_intelligence_tips(user.id, db),
        insights_service.get_trending_topics(user.id, db),
        insights_service.detect_activity_spikes(user.id, db),
    )

    return {
        "signals_processed": signals,
        "intelligence_tips": tips,
        "trending_topics": topics,
        "activity_spikes": spikes,
    }
