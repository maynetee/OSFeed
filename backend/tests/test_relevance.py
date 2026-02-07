import math
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from app.services.relevance_scoring import RelevanceScoringService


def _make_message(**kwargs):
    msg = MagicMock()
    msg.published_at = kwargs.get("published_at", datetime.now(timezone.utc))
    msg.is_duplicate = kwargs.get("is_duplicate", False)
    msg.originality_score = kwargs.get("originality_score", 100)
    msg.media_type = kwargs.get("media_type", None)
    msg.original_text = kwargs.get("original_text", "Hello world test message content")
    return msg


def _make_channel(**kwargs):
    ch = MagicMock()
    ch.subscriber_count = kwargs.get("subscriber_count", 10000)
    return ch


def test_compute_score_returns_between_0_and_1():
    msg = _make_message()
    ch = _make_channel()
    score = RelevanceScoringService.compute_score(msg, ch)
    assert 0.0 <= score <= 1.0


def test_recent_message_scores_higher_than_old():
    ch = _make_channel()
    recent = _make_message(published_at=datetime.now(timezone.utc))
    old = _make_message(published_at=datetime.now(timezone.utc) - timedelta(days=5))
    score_recent = RelevanceScoringService.compute_score(recent, ch)
    score_old = RelevanceScoringService.compute_score(old, ch)
    assert score_recent > score_old


def test_duplicate_message_scores_lower():
    ch = _make_channel()
    original = _make_message(is_duplicate=False, originality_score=100)
    duplicate = _make_message(is_duplicate=True, originality_score=0)
    score_original = RelevanceScoringService.compute_score(original, ch)
    score_duplicate = RelevanceScoringService.compute_score(duplicate, ch)
    assert score_original > score_duplicate


def test_high_subscriber_channel_scores_higher():
    msg = _make_message()
    big_ch = _make_channel(subscriber_count=1_000_000)
    small_ch = _make_channel(subscriber_count=100)
    score_big = RelevanceScoringService.compute_score(msg, big_ch)
    score_small = RelevanceScoringService.compute_score(msg, small_ch)
    assert score_big > score_small


def test_message_with_media_scores_higher():
    ch = _make_channel()
    with_media = _make_message(media_type="photo")
    without_media = _make_message(media_type=None)
    score_media = RelevanceScoringService.compute_score(with_media, ch)
    score_no_media = RelevanceScoringService.compute_score(without_media, ch)
    assert score_media > score_no_media


def test_longer_content_scores_higher():
    ch = _make_channel()
    long_msg = _make_message(original_text="x" * 500)
    short_msg = _make_message(original_text="hi")
    score_long = RelevanceScoringService.compute_score(long_msg, ch)
    score_short = RelevanceScoringService.compute_score(short_msg, ch)
    assert score_long > score_short


def test_no_published_at_uses_fallback():
    ch = _make_channel()
    msg = _make_message(published_at=None)
    score = RelevanceScoringService.compute_score(msg, ch)
    assert 0.0 <= score <= 1.0
    # Should be low since fallback = 168 hours old
    assert score < 0.7


def test_zero_subscribers_does_not_error():
    ch = _make_channel(subscriber_count=0)
    msg = _make_message()
    score = RelevanceScoringService.compute_score(msg, ch)
    assert 0.0 <= score <= 1.0
