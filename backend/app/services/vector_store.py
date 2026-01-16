from app.config import get_settings
from typing import Optional, Any
import uuid
import hashlib

settings = get_settings()


class VectorStore:
    def __init__(self):
        self.url = settings.qdrant_url
        self.api_key = settings.qdrant_api_key
        self.collection_name = settings.qdrant_collection_name
        self.distance = settings.qdrant_distance
        self.timeout_seconds = settings.qdrant_timeout_seconds
        self.model_name = settings.embedding_model
        self.dimension = settings.embedding_dimension
        self._embedder = None
        self._client = None
        self._ready = False
        self._init_collection()

    def _resolve_distance(self, qmodels: Any) -> Any:
        distance = (self.distance or "").lower()
        if distance in {"dot", "dotproduct", "inner"}:
            return qmodels.Distance.DOT
        if distance in {"euclid", "euclidean", "l2"}:
            return qmodels.Distance.EUCLID
        return qmodels.Distance.COSINE

    def _init_collection(self) -> None:
        if not self.url or not self.collection_name:
            return

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models as qmodels
        except Exception as e:
            print(f"Vector store init failed: {e}")
            return

        try:
            client = QdrantClient(
                url=self.url,
                api_key=self.api_key or None,
                timeout=self.timeout_seconds,
            )
            collections = client.get_collections().collections
            existing_names = {collection.name for collection in collections}
            if self.collection_name not in existing_names:
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.dimension,
                        distance=self._resolve_distance(qmodels),
                    ),
                )

            self._client = client
            self._ready = True
        except Exception as e:
            print(f"Vector store init failed: {e}")

    @property
    def is_ready(self) -> bool:
        return self._ready and self._client is not None

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

        from qdrant_client.http import models as qmodels
        texts = [item["text"] for item in items]
        vectors = self.embed_texts(texts)
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

        self._client.upsert(
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

    def query_similar(
        self,
        text: str,
        top_k: int = 5,
        filter: Optional[dict] = None,
    ) -> list[dict]:
        if not self.is_ready or not text:
            return []

        from qdrant_client.http import models as qmodels

        vector = self.embed_texts([text])[0]
        result = self._client.search(
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


# Singleton instance
vector_store = VectorStore()
