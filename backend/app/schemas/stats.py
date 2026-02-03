from pydantic import BaseModel, ConfigDict
from typing import List
from uuid import UUID


class StatsOverview(BaseModel):
    """Overview statistics for the dashboard."""
    total_messages: int
    active_channels: int
    messages_last_24h: int
    duplicates_last_24h: int

    model_config = ConfigDict(from_attributes=True)


class MessagesByDay(BaseModel):
    """Message count for a specific day."""
    date: str
    count: int

    model_config = ConfigDict(from_attributes=True)


class MessagesByChannel(BaseModel):
    """Message count for a specific channel."""
    channel_id: UUID
    channel_title: str
    count: int

    model_config = ConfigDict(from_attributes=True)


class TrustStats(BaseModel):
    """Trust metrics including primary sources and propaganda rates."""
    primary_sources_rate: float
    propaganda_rate: float
    verified_channels: int
    total_messages_24h: int

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    """Unified dashboard response containing all stats data."""
    overview: StatsOverview
    messages_by_day: List[MessagesByDay]
    messages_by_channel: List[MessagesByChannel]
    trust_stats: TrustStats

    model_config = ConfigDict(from_attributes=True)
