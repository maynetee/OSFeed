"""Escalation Scoring Service - LLM-powered message escalation detection.

Scores OSINT messages for escalation level using Gemini Flash for cost efficiency.
Considers aggressive language, military mobilization, diplomatic breakdowns, etc.
"""

import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.analysis import EscalationScore
from app.models.message import Message

logger = logging.getLogger(__name__)
settings = get_settings()

ESCALATION_PROMPT = (
    "Rate the escalation level of this OSINT intelligence message on a scale of 0.0 to 1.0. "
    "Consider: aggressive/threatening language, ultimatums, military mobilization mentions, "
    "diplomatic breakdown indicators, emergency language, weapons deployment, casualty reports. "
    "Return ONLY valid JSON: {\"score\": N, \"factors\": [\"reason1\", \"reason2\"]}"
)

BATCH_SIZE = 15


class EscalationScoringService:
    """Scores messages for escalation level using LLM analysis."""

    async def score_message(self, text: str) -> dict:
        """Score a single message for escalation.

        Args:
            text: The message text to analyze.

        Returns:
            Dict with score (float), level (str), and factors (list[str]).
        """
        if not text or not text.strip():
            return {"score": 0.0, "level": "low", "factors": []}

        if not settings.gemini_api_key:
            logger.warning("Gemini API key not configured, skipping escalation scoring")
            return {"score": 0.0, "level": "low", "factors": []}

        prompt = f"{ESCALATION_PROMPT}\n\nMessage:\n{text[:3000]}"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1},
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, params={"key": settings.gemini_api_key}, json=payload)
                response.raise_for_status()
                data = response.json()

            candidates = data.get("candidates") or []
            if not candidates:
                logger.warning("Gemini escalation scoring returned no candidates")
                return {"score": 0.0, "level": "low", "factors": []}

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts or "text" not in parts[0]:
                logger.warning("Gemini escalation scoring returned no text")
                return {"score": 0.0, "level": "low", "factors": []}

            raw_text = parts[0]["text"].strip()
            # Extract JSON from response (handle markdown code blocks)
            if "```" in raw_text:
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()

            result = json.loads(raw_text)
            score = max(0.0, min(1.0, float(result.get("score", 0.0))))
            factors = result.get("factors", [])
            if not isinstance(factors, list):
                factors = []

            if score > 0.7:
                level = "high"
            elif score > 0.5:
                level = "medium"
            else:
                level = "low"

            return {"score": score, "level": level, "factors": factors}

        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.error(f"Gemini API error during escalation scoring: {e}")
            return {"score": 0.0, "level": "low", "factors": []}
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse escalation score response: {e}")
            return {"score": 0.0, "level": "low", "factors": []}

    async def batch_score_new_messages(self):
        """Score unscored messages in batches."""
        try:
            async with AsyncSessionLocal() as session:
                # Find messages without escalation scores
                scored_ids_subq = select(EscalationScore.message_id).subquery()
                stmt = (
                    select(Message)
                    .where(
                        Message.id.notin_(select(scored_ids_subq)),
                        Message.original_text.isnot(None),
                    )
                    .order_by(Message.published_at.desc())
                    .limit(BATCH_SIZE)
                )
                result = await session.execute(stmt)
                messages = result.scalars().all()

                if not messages:
                    return

                logger.info(f"Scoring {len(messages)} messages for escalation")

                for message in messages:
                    text = message.translated_text or message.original_text
                    if not text or len(text.strip()) < 10:
                        # Store a default low score for very short messages
                        score_record = EscalationScore(
                            message_id=message.id,
                            score=0.0,
                            level="low",
                            factors=[],
                        )
                        session.add(score_record)
                        continue

                    score_data = await self.score_message(text)

                    score_record = EscalationScore(
                        message_id=message.id,
                        score=score_data["score"],
                        level=score_data["level"],
                        factors=score_data["factors"],
                    )
                    session.add(score_record)

                await session.commit()
                logger.info(f"Scored {len(messages)} messages for escalation")

        except SQLAlchemyError as e:
            logger.error(f"Database error during escalation scoring: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during escalation scoring: {e}")


# Singleton
escalation_service = EscalationScoringService()
