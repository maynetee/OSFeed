import json
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class StructuredSummaryService:
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = "gpt-4o-mini" 
        self.client = None
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_summary(self, texts: List[str]) -> Optional[Dict[str, Any]]:
        if not self.client or not texts:
            return None

        context_text = "\n\n".join(texts[:20])
        
        prompt = """
        You are an intelligence analyst. Analyze these messages and provide a structured summary in valid JSON format.
        Focus on geopolitical facts, conflicts, and major events. Ignore crypto/finance noise.
        
        Output format:
        {
            "headline": "Short, punchy title (max 10 words)",
            "bullets": ["Key point 1", "Key point 2", "Key point 3"],
            "context": "Brief background context (1-2 sentences)"
        }
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": context_text}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            return None
            
        except Exception as e:
            logger.error(f"Structured summary generation failed: {e}")
            return None
