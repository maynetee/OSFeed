import hashlib
import math
import re
import sys
import types
import uuid
from datetime import datetime, timedelta, timezone

if "sentence_transformers" not in sys.modules:
    sentence_stub = types.ModuleType("sentence_transformers")

    class _DummyEmbedder:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def encode(self, texts, normalize_embeddings=True):
            return [[0.0] for _ in texts]

    sentence_stub.SentenceTransformer = _DummyEmbedder
    sys.modules["sentence_transformers"] = sentence_stub

if "pinecone" not in sys.modules:
    pinecone_stub = types.ModuleType("pinecone")

    def _noop(*args, **kwargs):
        return None

    pinecone_stub.init = _noop
    pinecone_stub.list_indexes = lambda: []
    pinecone_stub.create_index = _noop
    pinecone_stub.describe_index = lambda name: {"status": {"ready": True}}

    class _DummyIndex:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def upsert(self, *args, **kwargs) -> None:
            return None

        def query(self, *args, **kwargs):
            return {"matches": []}

    pinecone_stub.Index = _DummyIndex
    sys.modules["pinecone"] = pinecone_stub

from app.models.channel import Channel  # noqa: F401
from app.models.message import Message
from app.services.deduplicator import DeduplicationService
import app.services.deduplicator as dedup_module


def _embed_text(text: str, dimensions: int = 64) -> list[float]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    vector = [0.0] * dimensions
    for token in tokens:
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        index = int(digest, 16) % dimensions
        vector[index] += 1.0
    norm = math.sqrt(sum(value * value for value in vector))
    if norm:
        vector = [value / norm for value in vector]
    return vector


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(l * r for l, r in zip(left, right))


class _FakeVectorStore:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, object]] = {}

    @property
    def is_ready(self) -> bool:
        return True

    def upsert_texts(self, items: list[dict]) -> list[str]:
        ids: list[str] = []
        for item in items:
            vector_id = str(item.get("id") or uuid.uuid4())
            self._items[vector_id] = {
                "vector": _embed_text(item["text"]),
                "metadata": item.get("metadata") or {},
            }
            ids.append(vector_id)
        return ids

    def query_similar(self, text: str, top_k: int = 5, filter: dict | None = None) -> list[dict]:
        query_vector = _embed_text(text)
        matches: list[dict] = []
        cutoff = None
        if filter:
            cutoff = filter.get("published_at_ts", {}).get("$gte")
        for vector_id, payload in self._items.items():
            metadata = payload["metadata"]
            if cutoff is not None:
                published_at_ts = metadata.get("published_at_ts")
                if published_at_ts is None or published_at_ts < cutoff:
                    continue
            score = _cosine_similarity(query_vector, payload["vector"])
            matches.append({"id": vector_id, "score": score, "metadata": metadata})
        matches.sort(key=lambda item: item["score"], reverse=True)
        return matches[:top_k]


def _build_message(channel_id: uuid.UUID, telegram_id: int, text: str, published_at: datetime) -> Message:
    return Message(
        id=uuid.uuid4(),
        channel_id=channel_id,
        telegram_message_id=telegram_id,
        original_text=text,
        published_at=published_at,
        fetched_at=published_at,
    )


def test_deduplication_marks_similar_messages(monkeypatch) -> None:
    fake_store = _FakeVectorStore()
    monkeypatch.setattr(dedup_module, "vector_store", fake_store)

    deduper = DeduplicationService(similarity_threshold=0.7)
    base_time = datetime.now(timezone.utc)
    channel_id = uuid.uuid4()

    message_a = _build_message(
        channel_id,
        100,
        "Authorities confirm explosion reported in Kyiv overnight.",
        base_time,
    )
    message_b = _build_message(
        channel_id,
        101,
        "Explosion reported in Kyiv overnight; authorities confirm.",
        base_time + timedelta(minutes=1),
    )
    message_c = _build_message(
        channel_id,
        102,
        "Sunny weather expected in Paris this weekend.",
        base_time + timedelta(minutes=2),
    )

    deduper.mark_duplicates([message_a, message_b, message_c])

    assert message_a.is_duplicate is False
    assert message_a.duplicate_group_id == message_a.id
    assert message_b.is_duplicate is True
    assert message_b.duplicate_group_id == message_a.id
    assert message_b.originality_score is not None and message_b.originality_score < 100
    assert message_c.is_duplicate is False
    assert message_c.duplicate_group_id is None
