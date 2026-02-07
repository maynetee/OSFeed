"""On-demand summarization service using Gemini Flash LLM."""

import json
import logging
import time
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SUMMARIZATION_PROMPT = (
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
    '}\n\n'
    "Messages to summarize:\n"
)

MAX_CHARS_PER_BATCH = 12000
MAX_MESSAGES_PER_BATCH = 50


async def _call_gemini(prompt: str, api_key: str, model: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3},
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, params={"key": api_key}, json=payload)
        response.raise_for_status()
        data = response.json()

    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini summarization returned no candidates")
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts or "text" not in parts[0]:
        raise RuntimeError("Gemini summarization returned no text")
    return parts[0]["text"].strip()


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
    # Try to extract JSON from the response
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
        # If JSON parsing fails, use raw text as summary
        return {
            "executive_summary": raw_text.strip(),
            "key_themes": [],
            "notable_events": [],
        }


async def generate_summary(
    messages: list[dict],
    model: Optional[str] = None,
) -> dict:
    """Generate a structured summary from a list of messages.

    Args:
        messages: List of message dicts with keys: original_text, translated_text, published_at, channel_title
        model: LLM model to use (defaults to Gemini Flash)

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

    api_key = settings.gemini_api_key
    model_name = model or settings.gemini_model
    if not api_key:
        raise RuntimeError("Gemini API key is not configured for summarization")

    start_time = time.time()

    # For large message sets, chunk and meta-summarize
    if len(messages) > MAX_MESSAGES_PER_BATCH:
        batch_summaries = []
        for i in range(0, len(messages), MAX_MESSAGES_PER_BATCH):
            batch = messages[i:i + MAX_MESSAGES_PER_BATCH]
            formatted = _format_messages_for_prompt(batch)
            prompt = SUMMARIZATION_PROMPT + formatted
            raw = await _call_gemini(prompt, api_key, model_name)
            parsed = _parse_llm_response(raw)
            batch_summaries.append(parsed["executive_summary"])

        # Meta-summarize all batch summaries
        meta_prompt = (
            "You are an OSINT analyst. Combine these partial summaries into a single coherent briefing.\n\n"
            "Return your response as valid JSON with this exact structure:\n"
            '{"executive_summary": "...", "key_themes": ["theme1", ...], "notable_events": ["event1", ...]}\n\n'
            "Partial summaries:\n" + "\n---\n".join(batch_summaries)
        )
        raw = await _call_gemini(meta_prompt, api_key, model_name)
        result = _parse_llm_response(raw)
    else:
        formatted = _format_messages_for_prompt(messages)
        prompt = SUMMARIZATION_PROMPT + formatted
        raw = await _call_gemini(prompt, api_key, model_name)
        result = _parse_llm_response(raw)

    elapsed = time.time() - start_time

    return {
        "executive_summary": result["executive_summary"],
        "key_themes": result["key_themes"],
        "notable_events": result["notable_events"],
        "model_used": model_name,
        "generation_time_seconds": round(elapsed, 2),
    }
