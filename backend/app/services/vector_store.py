from app.config import get_settings
from typing import Optional, Any
import time
import uuid
import hashlib

settings = get_settings()


class VectorStore:
    def __init__(self):
        self.api_key = settings.pinecone_api_key
        self.environment = settings.pinecone_environment
        self.index_name = settings.pinecone_index_name
        self.namespace = settings.pinecone_namespace
        self.metric = settings.pinecone_metric
        self.model_name = settings.embedding_model
        self.dimension = settings.embedding_dimension
        self._embedder = None
        self._index = None
        self._ready = False
        self._init_index()

    def _init_index(self) -> None:
        if not self.api_key or not self.index_name:
            return

        try:
            from pinecone import Pinecone, ServerlessSpec
        except Exception as e:
            print(f"Vector store init failed: {e}")
            return

        try:
            client = Pinecone(api_key=self.api_key)
            existing = client.list_indexes()
            existing_names = existing.names() if hasattr(existing, "names") else existing
            if self.index_name not in existing_names:
                client.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric=self.metric,
                    spec=ServerlessSpec(cloud="aws", region=self.environment),
                )
                while True:
                    description = client.describe_index(self.index_name)
                    status = description.status if hasattr(description, "status") else description.get("status", {})
                    ready = status.get("ready") if isinstance(status, dict) else getattr(status, "ready", False)
                    if ready:
                        break
                    time.sleep(1)

            self._index = client.Index(self.index_name)
            self._ready = True
        except Exception as e:
            print(f"Vector store init failed: {e}")

    @property
    def is_ready(self) -> bool:
        return self._ready and self._index is not None

    def _get_embedder(self) -> Any:
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(self.model_name)
        return self._embedder

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embedder = self._get_embedder()
        embeddings = embedder.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def upsert_texts(self, items: list[dict]) -> list[Optional[str]]:
        if not self.is_ready or not items:
            return [None] * len(items)

        texts = [item["text"] for item in items]
        vectors = self.embed_texts(texts)
        records = []
        ids = []

        for item, vector in zip(items, vectors):
            vector_id = item.get("id") or str(uuid.uuid4())
            metadata = item.get("metadata") or {}
            text_hash = hashlib.md5(item["text"].encode()).hexdigest()
            metadata.setdefault("text_hash", text_hash)
            records.append((str(vector_id), vector, metadata))
            ids.append(str(vector_id))

        self._index.upsert(vectors=records, namespace=self.namespace)
        return ids

    def query_similar(
        self,
        text: str,
        top_k: int = 5,
        filter: Optional[dict] = None,
    ) -> list[dict]:
        if not self.is_ready or not text:
            return []

        vector = self.embed_texts([text])[0]
        result = self._index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            namespace=self.namespace,
            filter=filter,
        )

        matches = result.get("matches") if isinstance(result, dict) else result.matches
        normalized = []
        for match in matches:
            if isinstance(match, dict):
                normalized.append(match)
            else:
                normalized.append(
                    {
                        "id": match.id,
                        "score": match.score,
                        "metadata": match.metadata,
                    }
                )
        return normalized


# Singleton instance
vector_store = VectorStore()
