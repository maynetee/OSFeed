import logging
from typing import List
from openai import AsyncOpenAI
from app.config import get_settings
from app.services.embedding.base import EmbeddingService

logger = logging.getLogger(__name__)
settings = get_settings()

class OpenAIEmbeddingService(EmbeddingService):
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.embedding_model or "text-embedding-3-small"
        self._dimension = settings.embedding_dimension or 1536
        self.client = None
        
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            logger.warning("OpenAI API key not found. Embedding service will fail if used.")

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not self.client:
            raise ValueError("OpenAI API key not configured")
            
        if not texts:
            return []

        try:
            cleaned_texts = [text.replace("\n", " ") for text in texts]
            
            response = await self.client.embeddings.create(
                input=cleaned_texts,
                model=self.model
            )
            
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise
