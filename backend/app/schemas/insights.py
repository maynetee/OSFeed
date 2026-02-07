from pydantic import BaseModel


class SignalsProcessed(BaseModel):
    today: int = 0
    this_week: int = 0
    all_time: int = 0


class IntelligenceTip(BaseModel):
    title: str
    description: str
    severity: str = "info"  # info, warning, critical


class TrendingTopic(BaseModel):
    topic: str
    count: int


class ActivitySpike(BaseModel):
    channel_id: str
    channel_title: str
    today_count: int
    daily_average: float
    ratio: float


class InsightsDashboardResponse(BaseModel):
    signals_processed: SignalsProcessed
    intelligence_tips: list[IntelligenceTip]
    trending_topics: list[TrendingTopic]
    activity_spikes: list[ActivitySpike]
