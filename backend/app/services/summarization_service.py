"""On-demand summarization service using OpenAI GPT (same model as translation)."""

import json
import logging
import time
from typing import Optional

from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = (
    "You are an OSINT analyst. "
    "Summarize the following intelligence messages into a structured briefing.\n\n"
    "Instructions:\n"
    "- Write an executive summary paragraph (3-5 sentences) covering the most important developments\n"
    "- Identify 3-8 key themes as short labels (e.g., \"Military escalation\", \"Diplomatic talks\")\n"
    "- List 3-10 notable events as brief descriptions (1 sentence each)\n"
    "- Focus on actionable intelligence and significant developments\n"
    "- Be factual and concise\n\n"
    "Return your response as valid JSON with this exact structure:\n"
    '{\n'
    '  "executive_summary": "...",\n'
    '  "key_themes": ["theme1", "theme2", ...],\n'
    '  "notable_events": ["event1", "event2", ...]\n'
    '}'
)

META_SYSTEM_PROMPT = (
    "You are an OSINT analyst. Combine these partial summaries into a single coherent briefing.\n\n"
    "Return your response as valid JSON with this exact structure:\n"
    '{"executive_summary": "...", "key_themes": ["theme1", ...], "notable_events": ["event1", ...]}'
)

MAX_MESSAGES_PER_BATCH = 50

# Lazy-initialized client
_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise RuntimeError("OpenAI API key is not configured for summarization")
        _client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=60.0)
    return _client


async def _call_openai(system: str, user_content: str, model: str) -> str:
    client = _get_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
    )
    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("OpenAI summarization returned no content")
    return text.strip()


def _format_messages_for_prompt(messages: list[dict]) -> str:
    lines = []
    for i, msg in enumerate(messages, 1):
        channel = msg.get("channel_title") or msg.get("channel_username") or "Unknown"
        date = msg.get("published_at", "")
        text = msg.get("translated_text") or msg.get("original_text") or ""
        if text:
            lines.append(f"[{i}] [{channel}] [{date}] {text[:500]}")
    return "\n".join(lines)


def _parse_llm_response(raw_text: str) -> dict:
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        result = json.loads(text)
        return {
            "executive_summary": result.get("executive_summary", text),
            "key_themes": result.get("key_themes", []),
            "notable_events": result.get("notable_events", []),
        }
    except (json.JSONDecodeError, KeyError):
        return {
            "executive_summary": raw_text.strip(),
            "key_themes": [],
            "notable_events": [],
        }


async def generate_summary(
    messages: list[dict],
    model: Optional[str] = None,
) -> dict:
    """Generate a structured summary from a list of messages using OpenAI.

    Args:
        messages: List of message dicts with keys: original_text, translated_text, published_at, channel_title
        model: LLM model to use (defaults to settings.openai_model, typically gpt-4o-mini)

    Returns:
        Dict with keys: executive_summary, key_themes, notable_events, model_used, generation_time_seconds
    """
    if not messages:
        return {
            "executive_summary": "No messages to summarize.",
            "key_themes": [],
            "notable_events": [],
            "model_used": None,
            "generation_time_seconds": 0.0,
        }

    model_name = model or settings.openai_model
    start_time = time.time()

    if len(messages) > MAX_MESSAGES_PER_BATCH:
        batch_summaries = []
        for i in range(0, len(messages), MAX_MESSAGES_PER_BATCH):
            batch = messages[i:i + MAX_MESSAGES_PER_BATCH]
            formatted = _format_messages_for_prompt(batch)
            raw = await _call_openai(SYSTEM_PROMPT, formatted, model_name)
            parsed = _parse_llm_response(raw)
            batch_summaries.append(parsed["executive_summary"])

        meta_content = "\n---\n".join(batch_summaries)
        raw = await _call_openai(META_SYSTEM_PROMPT, meta_content, model_name)
        result = _parse_llm_response(raw)
    else:
        formatted = _format_messages_for_prompt(messages)
        raw = await _call_openai(SYSTEM_PROMPT, formatted, model_name)
        result = _parse_llm_response(raw)

    elapsed = time.time() - start_time

    return {
        "executive_summary": result["executive_summary"],
        "key_themes": result["key_themes"],
        "notable_events": result["notable_events"],
        "model_used": model_name,
        "generation_time_seconds": round(elapsed, 2),
    }
