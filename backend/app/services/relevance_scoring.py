import math
from datetime import datetime, timezone

from app.models.channel import Channel
from app.models.message import Message


class RelevanceScoringService:
    WEIGHTS = {
        'recency': 0.30,
        'originality': 0.25,
        'channel_importance': 0.20,
        'media_richness': 0.15,
        'content_length': 0.10,
    }

    @staticmethod
    def compute_score(message: Message, channel: Channel) -> float:
        now = datetime.now(timezone.utc)

        # Recency: exponential decay
        if message.published_at:
            pub_at = message.published_at
            if pub_at.tzinfo is None:
                pub_at = pub_at.replace(tzinfo=timezone.utc)
            hours_old = max(0, (now - pub_at).total_seconds() / 3600)
        else:
            hours_old = 168  # 7 days fallback

        recency = max(0.1, math.exp(-0.02 * hours_old))

        # Originality
        if message.is_duplicate:
            originality = 0.0
        else:
            originality = (message.originality_score or 100) / 100.0

        # Channel importance (log scale of subscribers)
        subs = channel.subscriber_count or 0
        channel_importance = min(1.0, math.log10(max(subs, 1)) / 7.0)

        # Media richness
        media_richness = 0.8 if message.media_type else 0.3

        # Content length
        text_len = len(message.original_text or '')
        content_length = min(1.0, text_len / 500.0)

        factors = {
            'recency': recency,
            'originality': originality,
            'channel_importance': channel_importance,
            'media_richness': media_richness,
            'content_length': content_length,
        }

        score = sum(RelevanceScoringService.WEIGHTS[k] * v for k, v in factors.items())
        return round(min(1.0, max(0.0, score)), 4)
