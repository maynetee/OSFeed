from typing import Optional, Dict, Any
from decimal import Decimal
import logging

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.api_usage import ApiUsage

logger = logging.getLogger(__name__)
settings = get_settings()


def _calculate_cost(prompt_tokens: int, completion_tokens: int) -> Decimal:
    input_rate = Decimal(str(settings.llm_cost_input_per_1k))
    output_rate = Decimal(str(settings.llm_cost_output_per_1k))
    prompt_cost = Decimal(prompt_tokens) * input_rate / Decimal(1000)
    completion_cost = Decimal(completion_tokens) * output_rate / Decimal(1000)
    return prompt_cost + completion_cost


async def record_api_usage(
    provider: str,
    model: str,
    purpose: str,
    prompt_tokens: int,
    completion_tokens: int,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    if not settings.api_usage_tracking_enabled:
        return

    total_tokens = prompt_tokens + completion_tokens
    estimated_cost = _calculate_cost(prompt_tokens, completion_tokens)

    async with AsyncSessionLocal() as session:
        try:
            session.add(
                ApiUsage(
                    provider=provider,
                    model=model,
                    purpose=purpose,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    estimated_cost_usd=estimated_cost,
                    metadata=metadata,
                )
            )
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Failed to record API usage")
