"""Pattern Detection Service for intelligence analysis.

Detects volume spikes, entity emergence, and narrative shifts
from collected messages.
"""

import logging
import re
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.analysis import DetectedPattern
from app.models.channel import Channel
from app.models.message import Message

logger = logging.getLogger(__name__)


class PatternDetectionService:
    """Detects intelligence patterns across collected messages."""

    # Words to ignore when detecting entity emergence
    STOP_WORDS = frozenset({
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "it", "this", "that", "was", "are",
        "been", "be", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "shall", "can", "not", "no", "all",
        "each", "every", "both", "few", "more", "most", "other", "some", "such",
        "than", "too", "very", "just", "about", "above", "after", "again", "also",
        "any", "because", "before", "between", "during", "here", "how", "into",
        "its", "new", "now", "only", "out", "over", "said", "same", "so", "still",
        "these", "they", "them", "then", "there", "those", "through", "under",
        "what", "when", "where", "which", "while", "who", "whom", "why", "you",
        "your", "his", "her", "our", "their", "its", "one", "two", "three",
        "being", "get", "got", "like", "make", "made", "many", "much", "own",
        "well", "way", "even", "back", "going", "come", "went", "take", "see",
    })

    # Regex for potential entity names (capitalized words, 2+ chars)
    ENTITY_PATTERN = re.compile(r"\b[A-Z][a-zA-Z]{2,}\b")

    async def detect_volume_spikes(self, db: AsyncSession) -> list[DetectedPattern]:
        """Detect when message volume for a channel spikes above 2 standard deviations.

        Algorithm:
        1. Query message counts per channel for last 24h
        2. Query 7-day rolling average per channel
        3. Flag channels where today's count > avg + 2*stddev
        4. Create DetectedPattern with type='volume_spike'
        """
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(hours=24)
        week_ago = now - timedelta(days=7)

        # Get recent count and 7-day count per channel in one query
        result = await db.execute(
            select(
                Channel.id.label("channel_id"),
                Channel.title.label("channel_title"),
                func.coalesce(
                    func.sum(case((Message.published_at >= day_ago, 1), else_=0)),
                    0,
                ).label("recent_count"),
                func.coalesce(
                    func.sum(case((Message.published_at >= week_ago, 1), else_=0)),
                    0,
                ).label("week_count"),
            )
            .select_from(Message)
            .join(Channel, Message.channel_id == Channel.id)
            .where(Message.published_at >= week_ago)
            .group_by(Channel.id, Channel.title)
        )
        rows = result.all()

        patterns = []
        for row in rows:
            daily_avg = row.week_count / 7.0 if row.week_count > 0 else 0
            if daily_avg < 2:
                # Skip low-activity channels
                continue

            if row.recent_count <= 0:
                continue

            ratio = row.recent_count / daily_avg
            if ratio <= 2.0:
                continue

            # Check if we already have a recent spike pattern for this channel
            existing = await db.execute(
                select(DetectedPattern)
                .where(
                    DetectedPattern.pattern_type == "volume_spike",
                    DetectedPattern.title.contains(str(row.channel_title)),
                    DetectedPattern.detected_at >= day_ago,
                )
                .limit(1)
            )
            if existing.scalar_one_or_none():
                continue

            # Get sample message IDs from this channel in the spike period
            sample_result = await db.execute(
                select(Message.id)
                .where(
                    Message.channel_id == row.channel_id,
                    Message.published_at >= day_ago,
                )
                .order_by(Message.published_at.desc())
                .limit(5)
            )
            sample_ids = [str(mid) for (mid,) in sample_result.all()]

            confidence = min(0.95, 0.5 + (ratio - 2.0) * 0.1)
            pattern = DetectedPattern(
                id=uuid.uuid4(),
                pattern_type="volume_spike",
                title=f"Volume spike: {row.channel_title}",
                description=(
                    f"Channel '{row.channel_title}' has {row.recent_count} messages in the last 24h, "
                    f"which is {ratio:.1f}x the 7-day daily average of {daily_avg:.1f}."
                ),
                evidence_message_ids=sample_ids,
                confidence=round(confidence, 2),
                detected_at=now,
                expires_at=now + timedelta(days=2),
            )
            db.add(pattern)
            patterns.append(pattern)

        return patterns

    async def detect_entity_emergence(self, db: AsyncSession) -> list[DetectedPattern]:
        """Detect new entities appearing across multiple sources.

        Algorithm:
        1. Get messages from last 12 hours with translated_text
        2. Extract capitalized words as potential entity names
        3. Compare frequency with historical baseline (7-day average)
        4. Flag entities appearing 3x more than usual across 2+ channels
        """
        now = datetime.now(timezone.utc)
        hours_12_ago = now - timedelta(hours=12)
        week_ago = now - timedelta(days=7)

        # Get recent messages with text
        recent_result = await db.execute(
            select(
                Message.channel_id,
                func.coalesce(Message.translated_text, Message.original_text).label("text"),
            )
            .where(
                Message.published_at >= hours_12_ago,
                Message.original_text.isnot(None),
            )
            .limit(500)
        )
        recent_rows = recent_result.all()

        if not recent_rows:
            return []

        # Extract entities from recent messages, tracking which channels mention them
        recent_entities: dict[str, set[str]] = {}
        for row in recent_rows:
            if not row.text:
                continue
            entities = self.ENTITY_PATTERN.findall(row.text)
            for entity in entities:
                if entity.lower() in self.STOP_WORDS or len(entity) < 3:
                    continue
                if entity not in recent_entities:
                    recent_entities[entity] = set()
                recent_entities[entity].add(str(row.channel_id))

        # Filter: must appear in 2+ channels
        multi_channel_entities = {
            e: channels for e, channels in recent_entities.items()
            if len(channels) >= 2
        }

        if not multi_channel_entities:
            return []

        # Get baseline: count entity mentions from the prior 7 days
        baseline_result = await db.execute(
            select(
                func.coalesce(Message.translated_text, Message.original_text).label("text"),
            )
            .where(
                Message.published_at >= week_ago,
                Message.published_at < hours_12_ago,
                Message.original_text.isnot(None),
            )
            .limit(2000)
        )
        baseline_rows = baseline_result.all()

        baseline_counts: Counter = Counter()
        for (text,) in baseline_rows:
            if not text:
                continue
            for entity in self.ENTITY_PATTERN.findall(text):
                if entity.lower() not in self.STOP_WORDS and len(entity) >= 3:
                    baseline_counts[entity] += 1

        # Normalize baseline to 12h equivalent
        baseline_period_hours = max(1, (now - week_ago).total_seconds() / 3600 - 12)
        normalization_factor = 12.0 / baseline_period_hours

        # Find emerging entities (3x+ more frequent than baseline)
        patterns = []
        for entity, channels in multi_channel_entities.items():
            recent_count = len(channels)  # Use channel count as proxy for importance
            baseline_normalized = baseline_counts.get(entity, 0) * normalization_factor

            if baseline_normalized < 0.5:
                # New entity not seen in baseline
                emergence_ratio = float(recent_count)
            else:
                emergence_ratio = recent_count / baseline_normalized

            if emergence_ratio < 3.0:
                continue

            # Check for existing pattern
            existing = await db.execute(
                select(DetectedPattern)
                .where(
                    DetectedPattern.pattern_type == "entity_emergence",
                    DetectedPattern.title.contains(entity),
                    DetectedPattern.detected_at >= hours_12_ago,
                )
                .limit(1)
            )
            if existing.scalar_one_or_none():
                continue

            confidence = min(0.9, 0.4 + len(channels) * 0.1 + min(emergence_ratio * 0.05, 0.3))
            pattern = DetectedPattern(
                id=uuid.uuid4(),
                pattern_type="entity_emergence",
                title=f"Emerging entity: {entity}",
                description=(
                    f"Entity '{entity}' appeared across {len(channels)} channels "
                    f"in the last 12 hours, {emergence_ratio:.1f}x above baseline."
                ),
                evidence_message_ids=[],
                confidence=round(confidence, 2),
                detected_at=now,
                expires_at=now + timedelta(days=1),
            )
            db.add(pattern)
            patterns.append(pattern)

        # Limit to top 5 by confidence
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        return patterns[:5]

    async def run_detection(self):
        """Run all pattern detection algorithms."""
        async with AsyncSessionLocal() as db:
            try:
                spikes = await self.detect_volume_spikes(db)
                entities = await self.detect_entity_emergence(db)
                await db.commit()
                logger.info(
                    f"Pattern detection complete: {len(spikes)} volume spikes, "
                    f"{len(entities)} entity patterns"
                )
            except Exception as e:
                logger.error(f"Pattern detection failed: {e}")
                await db.rollback()


pattern_service = PatternDetectionService()
