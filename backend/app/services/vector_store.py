import logging
from app.config import get_settings
from typing import Optional, Any, List
import uuid
import hashlib
import asyncio
from app.services.embedding.openai import OpenAIEmbeddingService

settings = get_settings()
logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.url = settings.qdrant_url
        self.api_key = settings.qdrant_api_key
        self.collection_name = settings.qdrant_collection_name
        self.distance = settings.qdrant_distance
        self.timeout_seconds = settings.qdrant_timeout_seconds
        
        self._embedder = OpenAIEmbeddingService()
        self.dimension = self._embedder.dimension
        
        self._client = None
        self._ready = False
        # Initialization happens lazily to support async

    def _resolve_distance(self, qmodels: Any) -> Any:
        distance = (self.distance or "").lower()
        if distance in {"dot", "dotproduct", "inner"}:
            return qmodels.Distance.DOT
        if distance in {"euclid", "euclidean", "l2"}:
            return qmodels.Distance.EUCLID
        return qmodels.Distance.COSINE

    async def _ensure_collection(self) -> None:
        if self._ready:
            return
            
        if not self.url or not self.collection_name:
            return

        try:
            from qdrant_client import AsyncQdrantClient
            from qdrant_client.http import models as qmodels
        except ImportError as e:
            logger.error(f"Vector store init failed: {e}")
            return

        try:
            if not self._client:
                self._client = AsyncQdrantClient(
                    url=self.url,
                    api_key=self.api_key or None,
                    timeout=self.timeout_seconds,
                )

            # Check if collection exists
            # AsyncQdrantClient methods are async
            collections_response = await self._client.get_collections()
            collections = collections_response.collections
            existing_names = {collection.name for collection in collections}
            
            if self.collection_name not in existing_names:
                await self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.dimension,
                        distance=self._resolve_distance(qmodels),
                    ),
                )

            self._ready = True
        except Exception as e:
            logger.error(f"Vector store init failed: {e}")

    @property
    def is_ready(self) -> bool:
        # Note: This property is less useful now since init is lazy/async
        # But we can check if client is instantiated
        return self._client is not None

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return await self._embedder.embed_texts(texts)

    async def upsert_texts(self, items: list[dict]) -> list[Optional[str]]:
        await self._ensure_collection()
        
        if not self._ready or not items:
            return [None] * len(items)

        from qdrant_client.http import models as qmodels
        texts = [item["text"] for item in items]
        vectors = await self.embed_texts(texts)
        records: list[qmodels.PointStruct] = []
        ids = []

        for item, vector in zip(items, vectors):
            vector_id = item.get("id") or str(uuid.uuid4())
            metadata = item.get("metadata") or {}
            text_hash = hashlib.md5(item["text"].encode()).hexdigest()
            metadata.setdefault("text_hash", text_hash)
            records.append(
                qmodels.PointStruct(
                    id=str(vector_id),
                    vector=vector,
                    payload=metadata,
                )
            )
            ids.append(str(vector_id))

        await self._client.upsert(
            collection_name=self.collection_name,
            points=records,
            wait=True,
        )
        return ids

    def _build_filter(self, raw_filter: Optional[dict], qmodels: Any) -> Optional[Any]:
        if not raw_filter:
            return None

        conditions = []
        for key, condition in raw_filter.items():
            if isinstance(condition, dict):
                if "$eq" in condition:
                    conditions.append(
                        qmodels.FieldCondition(
                            key=key,
                            match=qmodels.MatchValue(value=condition["$eq"]),
                        )
                    )
                    continue
                if "$in" in condition:
                    conditions.append(
                        qmodels.FieldCondition(
                            key=key,
                            match=qmodels.MatchAny(any=condition["$in"]),
                        )
                    )
                    continue

                range_kwargs = {}
                if "$gte" in condition:
                    range_kwargs["gte"] = condition["$gte"]
                if "$gt" in condition:
                    range_kwargs["gt"] = condition["$gt"]
                if "$lte" in condition:
                    range_kwargs["lte"] = condition["$lte"]
                if "$lt" in condition:
                    range_kwargs["lt"] = condition["$lt"]
                if range_kwargs:
                    conditions.append(
                        qmodels.FieldCondition(
                            key=key,
                            range=qmodels.Range(**range_kwargs),
                        )
                    )
            else:
                conditions.append(
                    qmodels.FieldCondition(
                        key=key,
                        match=qmodels.MatchValue(value=condition),
                    )
                )

        if not conditions:
            return None
        return qmodels.Filter(must=conditions)

    async def query_similar(
        self,
        text: str,
        top_k: int = 5,
        filter: Optional[dict] = None,
    ) -> list[dict]:
        await self._ensure_collection()
        
        if not self._ready or not text:
            return []

        from qdrant_client.http import models as qmodels

        vectors = await self.embed_texts([text])
        vector = vectors[0]
        
        result = await self._client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=top_k,
            with_payload=True,
            query_filter=self._build_filter(filter, qmodels),
        )

        normalized = []
        for match in result:
            normalized.append(
                {
                    "id": str(match.id),
                    "score": match.score,
                    "metadata": match.payload or {},
                }
            )
        return normalized

    async def get_or_create_embedding(self, text: str, doc_id: str) -> List[float]:
        await self._ensure_collection()
        if not self._ready:
            return []

        from qdrant_client.http import models as qmodels
        
        # Check if exists
        try:
            points = await self._client.retrieve(
                collection_name=self.collection_name,
                ids=[doc_id],
                with_vectors=True
            )
            
            if points and points[0].vector:
                return points[0].vector
        except Exception:
            pass # Not found or error, proceed to create

        # Create
        try:
            embeddings = await self._embedder.embed_texts([text])
            if not embeddings:
                return []
                
            vector = embeddings[0]
            
            # Upsert immediately to save it
            await self._client.upsert(
                collection_name=self.collection_name,
                points=[
                    qmodels.PointStruct(
                        id=doc_id,
                        vector=vector,
                        payload={"text": text[:100]} # Minimal payload
                    )
                ]
            )
            return vector
        except Exception as e:
            logger.error(f"Failed to get/create embedding: {e}")
            return []

    async def scroll_vectors(
        self,
        limit: int = 100,
        offset: Optional[str] = None,
        filter: Optional[dict] = None,
        with_vectors: bool = False
    ) -> tuple[list[dict], Optional[str]]:
        """Fetch vectors with pagination for batch processing."""
        await self._ensure_collection()
        
        if not self._ready:
            return [], None

        from qdrant_client.http import models as qmodels
        
        result, next_page_offset = await self._client.scroll(
            collection_name=self.collection_name,
            scroll_filter=self._build_filter(filter, qmodels),
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=with_vectors,
        )

        normalized = []
        for point in result:
            normalized.append({
                "id": str(point.id),
                "payload": point.payload or {},
                "vector": point.vector if with_vectors else None
            })
            
        return normalized, next_page_offset

vector_store = VectorStore()
