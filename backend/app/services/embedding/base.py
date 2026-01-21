from abc import ABC, abstractmethod
from typing import List

class EmbeddingService(ABC):
    """Abstract base class for embedding services."""

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of the embeddings."""
        pass
