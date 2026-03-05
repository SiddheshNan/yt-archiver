"""
Channel repository — data access layer for the channels collection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.results import InsertOneResult

from app.database import Database
from app.logging_config import get_logger

logger = get_logger(__name__)


class ChannelRepository:
    """Data access layer for the channels MongoDB collection."""

    def __init__(self, db: Database) -> None:
        self._collection: Collection = db.channels

    # ── Create ──────────────────────────────────────────────────────────

    def create(self, document: dict[str, Any]) -> str:
        """Insert a new channel document.

        Returns:
            The inserted document's ObjectId as a string.
        """
        result: InsertOneResult = self._collection.insert_one(document)
        logger.info(
            "channel_created",
            youtube_channel_id=document.get("youtube_channel_id"),
            id=str(result.inserted_id),
        )
        return str(result.inserted_id)

    # ── Read ────────────────────────────────────────────────────────────

    def find_by_id(self, id: str) -> dict[str, Any] | None:
        """Find a channel by its MongoDB ObjectId string."""
        if not ObjectId.is_valid(id):
            return None
        return self._collection.find_one({"_id": ObjectId(id)})

    def find_by_youtube_id(self, youtube_channel_id: str) -> dict[str, Any] | None:
        """Find a channel by its YouTube channel ID."""
        return self._collection.find_one({"youtube_channel_id": youtube_channel_id})

    def list_all(
        self,
        skip: int = 0,
        limit: int = 50,
        sort_by: str = "name",
        sort_order: int = 1,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return a paginated list of channels with total count.

        Args:
            skip: Number of documents to skip.
            limit: Maximum documents to return.
            sort_by: Field to sort by (default: name ascending).
            sort_order: 1 for ascending, -1 for descending.

        Returns:
            Tuple of (list of channel documents, total count).
        """
        total = self._collection.count_documents({})
        cursor = (
            self._collection.find()
            .sort(sort_by, sort_order)
            .skip(skip)
            .limit(limit)
        )
        return list(cursor), total

    # ── Update ──────────────────────────────────────────────────────────

    def increment_video_count(self, id: str, delta: int = 1) -> bool:
        """Increment (or decrement) the video_count for a channel.

        Args:
            id: MongoDB ObjectId string.
            delta: Amount to increment by (use -1 to decrement).

        Returns:
            True if a document was modified.
        """
        result = self._collection.update_one(
            {"_id": ObjectId(id)},
            {
                "$inc": {"video_count": delta},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        return result.modified_count > 0

    def update(self, id: str, fields: dict[str, Any]) -> bool:
        """Update arbitrary fields on a channel.

        Args:
            id: MongoDB ObjectId string.
            fields: Dict of field names to new values.

        Returns:
            True if a document was modified.
        """
        if not ObjectId.is_valid(id):
            return False
        fields["updated_at"] = datetime.now(timezone.utc)
        result = self._collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": fields},
        )
        return result.modified_count > 0

    # ── Delete ──────────────────────────────────────────────────────────

    def delete(self, id: str) -> bool:
        """Delete a channel by its MongoDB ObjectId string.

        Returns:
            True if a document was deleted.
        """
        if not ObjectId.is_valid(id):
            return False
        result = self._collection.delete_one({"_id": ObjectId(id)})
        logger.info("channel_deleted", id=id, deleted=result.deleted_count > 0)
        return result.deleted_count > 0
