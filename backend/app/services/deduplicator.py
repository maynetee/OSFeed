from typing import List, Optional
from app.models.message import Message
from app.services.vector_store import vector_store
from app.config import get_settings
from datetime import datetime, timezone
import uuid

settings = get_settings()


class DeduplicationService:
    def __init__(self, similarity_threshold: Optional[float] = None):
        """
        Initialize deduplication service

        Args:
            similarity_threshold: Minimum similarity ratio (0-1) to consider messages as duplicates
        """
        self.similarity_threshold = similarity_threshold or settings.dedup_similarity_threshold
        self.top_k = settings.dedup_top_k

    def _get_message_text(self, message: Message) -> str:
        return message.translated_text or message.original_text or ""

    def _message_timestamp(self, message: Message) -> Optional[int]:
        timestamp = message.published_at or message.fetched_at
        if not timestamp:
            return None
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return int(timestamp.timestamp())

    def mark_duplicates(
        self,
        messages: List[Message],
        cutoff_time: Optional[datetime] = None,
    ) -> List[Message]:
        """
        Mark messages as duplicates and assign group IDs

        Returns:
            Updated list of messages
        """
        if len(messages) <= 1:
            return messages

        if not vector_store.is_ready:
            return messages

        def _sort_key(msg: Message) -> int:
            ts = msg.published_at or msg.fetched_at
            if not ts:
                return 0
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return int(ts.timestamp())

        messages_sorted = sorted(messages, key=_sort_key)
        message_lookup = {str(msg.id): msg for msg in messages_sorted}
        cutoff_ts = int(cutoff_time.timestamp()) if cutoff_time else None

        for message in messages_sorted:
            text = self._get_message_text(message)
            if not text:
                continue

            if not message.embedding_id:
                published_at_ts = self._message_timestamp(message)
                metadata = {
                    "message_id": str(message.id),
                    "channel_id": str(message.channel_id),
                }
                if published_at_ts is not None:
                    metadata["published_at_ts"] = published_at_ts

                embedding_id = vector_store.upsert_texts(
                    [
                        {
                            "id": str(message.id),
                            "text": text,
                            "metadata": metadata,
                        }
                    ]
                )[0]
                if embedding_id:
                    message.embedding_id = embedding_id

            query_filter = {"published_at_ts": {"$gte": cutoff_ts}} if cutoff_ts else None
            matches = vector_store.query_similar(
                text,
                top_k=self.top_k,
                filter=query_filter,
            )

            best_match = None
            for match in matches:
                match_id = str(match.get("id"))
                score = match.get("score")
                if match_id == str(message.id):
                    continue
                if score is None or score < self.similarity_threshold:
                    continue
                if best_match is None or score > best_match["score"]:
                    best_match = {"id": match_id, "score": score}

            if best_match:
                match_id = best_match["id"]
                matched_message = message_lookup.get(match_id)

                if matched_message and matched_message.duplicate_group_id:
                    group_id = matched_message.duplicate_group_id
                elif matched_message:
                    group_id = matched_message.id
                    matched_message.duplicate_group_id = group_id
                    matched_message.is_duplicate = False
                    matched_message.originality_score = 100
                else:
                    try:
                        group_id = uuid.UUID(match_id)
                    except ValueError:
                        group_id = uuid.uuid4()

                message.is_duplicate = True
                message.duplicate_group_id = group_id
                message.originality_score = max(0, min(100, int((1 - best_match["score"]) * 100)))
            else:
                message.is_duplicate = False
                message.duplicate_group_id = None
                message.originality_score = 100

        return messages


# Singleton instance
deduplicator = DeduplicationService()
