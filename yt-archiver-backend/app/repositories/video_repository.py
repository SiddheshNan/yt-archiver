"""
Video repository — data access layer for the videos collection.

All MongoDB operations for videos are encapsulated here.
This keeps the service layer clean and database-agnostic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

from app.database import Database
from app.logging_config import get_logger
from app.models.video import VideoStatus

logger = get_logger(__name__)


class VideoRepository:
    """Data access layer for the videos MongoDB collection."""

    def __init__(self, db: Database) -> None:
        self._collection: Collection = db.videos

    # ── Create ──────────────────────────────────────────────────────────

    def create(self, document: dict[str, Any]) -> str:
        """Insert a new video document.

        Returns:
            The inserted document's ObjectId as a string.
        """
        result: InsertOneResult = self._collection.insert_one(document)
        logger.info("video_created", video_id=document.get(
            "video_id"), id=str(result.inserted_id))
        return str(result.inserted_id)

    # ── Read ────────────────────────────────────────────────────────────

    def find_by_id(self, id: str) -> dict[str, Any] | None:
        """Find a video by its MongoDB ObjectId string."""
        if not ObjectId.is_valid(id):
            return None
        return self._collection.find_one({"_id": ObjectId(id)})

    def find_by_video_id(self, video_id: str) -> dict[str, Any] | None:
        """Find a video by its YouTube video ID."""
        return self._collection.find_one({"video_id": video_id})

    def list_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: int = -1,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return a paginated list of videos with total count.

        Args:
            skip: Number of documents to skip.
            limit: Maximum documents to return.
            sort_by: Field to sort by.
            sort_order: 1 for ascending, -1 for descending.
            filters: Optional MongoDB query filters.

        Returns:
            Tuple of (list of video documents, total count).
        """
        query = filters or {}
        total = self._collection.count_documents(query)
        cursor = (
            self._collection.find(query)
            .sort(sort_by, sort_order)
            .skip(skip)
            .limit(limit)
        )
        return list(cursor), total

    def find_by_channel(
        self,
        channel_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """List videos belonging to a specific channel (paginated).

        Args:
            channel_id: MongoDB ObjectId string of the channel.
            skip: Number of documents to skip.
            limit: Maximum documents to return.

        Returns:
            Tuple of (list of video documents, total count).
        """
        if not ObjectId.is_valid(channel_id):
            return [], 0
        query = {"channel_id": ObjectId(channel_id)}
        total = self._collection.count_documents(query)
        cursor = (
            self._collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return list(cursor), total

    def search(
        self,
        query_text: str,
        channel_id: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """Full-text search across video title, description, and channel name.

        Args:
            query_text: Search query string.
            channel_id: Optional channel filter (MongoDB ObjectId string).
            skip: Number of documents to skip.
            limit: Maximum documents to return.

        Returns:
            Tuple of (list of matching documents, total count).
        """
        import re
        regex_pattern = re.compile(query_text, re.IGNORECASE)

        candidates: dict[str, dict[str, Any]] = {}

        # 1. Full-text search (semantic/token matches)
        text_query: dict[str, Any] = {"$text": {"$search": query_text}}
        if channel_id and ObjectId.is_valid(channel_id):
            text_query["channel_id"] = ObjectId(channel_id)

        try:
            text_cursor = (
                self._collection.find(
                    text_query, {"score": {"$meta": "textScore"}})
                .sort([("score", {"$meta": "textScore"})])
                .limit(limit * 2)  # Fetch extra to account for merging
            )
            for doc in text_cursor:
                doc_id = str(doc["_id"])
                doc["_search_score"] = doc["score"]
                candidates[doc_id] = doc
        except Exception:
            # $text index might not be created or query might be invalid
            pass

        # 2. Regex search (partial substring matches)
        regex_query: dict[str, Any] = {
            "$or": [
                {"title": {"$regex": regex_pattern}},
                {"channel_name": {"$regex": regex_pattern}},
            ]
        }
        if channel_id and ObjectId.is_valid(channel_id):
            regex_query["channel_id"] = ObjectId(channel_id)

        regex_cursor = (
            self._collection.find(regex_query)
            .sort("created_at", -1)
            .limit(limit * 2)
        )
        for doc in regex_cursor:
            doc_id = str(doc["_id"])
            if doc_id not in candidates:
                # Assign a synthetic score for pure substring matches
                # Text scores are usually 0.5 - 5.0. A substring match is pretty good.
                doc["_search_score"] = 1.5
                candidates[doc_id] = doc
            else:
                # If it matched BOTH text and regex, give it a tiny boost
                candidates[doc_id]["_search_score"] += 0.5

        # Sort combined results descending by search score
        sorted_candidates = sorted(
            candidates.values(),
            key=lambda x: x.get("_search_score", 0),
            reverse=True
        )

        # Approximate total since we capped at limit * 2
        total = len(sorted_candidates)

        # Apply pagination
        paginated_results = sorted_candidates[skip: skip + limit]

        return paginated_results, total

    # ── Recommendations ─────────────────────────────────────────────────

    def get_home_recommendations(
        self, limit: int = 24, exclude_ids: list[str] = []
    ) -> list[dict[str, Any]]:
        """Get intelligent video recommendations for the home page.

        Scores videos based on the user's globally most frequent tags and categories,
        while maintaining some randomness for discoverability.

        Args:
            limit: Number of videos to return.
            exclude_ids: List of video ObjectIds to exclude (for pagination).

        Returns:
            List of video documents.
        """
        import random

        # 1. Get Top 5 Categories & Top 10 Tags across the entire library
        # We use a lightweight aggregation.
        top_cats = []
        top_tags = []

        try:
            cat_pipeline = [
                {"$unwind": "$categories"},
                {"$group": {"_id": "$categories", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            tag_pipeline = [
                {"$unwind": "$tags"},
                {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            top_cats = [doc["_id"].lower()
                        for doc in self._collection.aggregate(cat_pipeline)]
            top_tags = [doc["_id"].lower()
                        for doc in self._collection.aggregate(tag_pipeline)]
        except Exception:
            pass  # Failsafe if DB is empty or lacks fields

        target_cats = set(top_cats)
        target_tags = set(top_tags)

        # 2. Fetch candidates (larger pool than requested limit, explicitly excluding what's already on screen)
        match_stage: dict[str, Any] = {}
        if exclude_ids:
            obj_ids = [ObjectId(id)
                       for id in exclude_ids if ObjectId.is_valid(id)]
            if obj_ids:
                match_stage = {"_id": {"$nin": obj_ids}}

        # Get x3 the limit to have a good pool to score
        candidates_cursor = (
            self._collection.find(match_stage)
            .sort("created_at", -1)
            .limit(limit * 3)
        )

        candidates = list(candidates_cursor)

        # 3. Score the candidates
        for doc in candidates:
            score = random.uniform(0, 5)  # Base random padding for variety

            # Boost for sharing popular categories
            doc_cats = doc.get("categories", [])
            for c in doc_cats:
                if c.lower() in target_cats:
                    score += 3

            # Boost for sharing popular tags
            doc_tags = doc.get("tags", [])
            for t in doc_tags:
                if t.lower() in target_tags:
                    score += 2

            doc["_home_score"] = score

        # 4. Sort and return
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get("_home_score", 0),
            reverse=True
        )

        return sorted_candidates[:limit]

    def get_related_videos(
        self,
        current_video_id: str,
        channel_id: str,
        title: str,
        tags: list[str],
        categories: list[str],
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get related videos for the watch page using a scoring engine.

        Scoring points:
        - Shared Tag: +3 points per tag
        - Shared Category: +2 points per category
        - Same Channel: +2 points
        - Title text match: +1 point base (plus scaled textScore)
        """
        if not ObjectId.is_valid(current_video_id):
            return []

        vid_obj_id = ObjectId(current_video_id)
        candidates: dict[str, dict[str, Any]] = {}

        # Helper to fetch and merge candidates
        def fetch_candidates(cursor, base_score=0, is_text_search=False):
            for doc in cursor:
                doc_id = str(doc["_id"])
                if doc_id not in candidates:
                    doc["_relevance_score"] = 0
                    candidates[doc_id] = doc

                candidates[doc_id]["_relevance_score"] += base_score
                if is_text_search and "score" in doc:
                    # add text search score (usually between 0.5 and 5.0)
                    candidates[doc_id]["_relevance_score"] += doc["score"]

        # 1. Fetch candidates from the same channel
        if ObjectId.is_valid(channel_id):
            chan_cursor = self._collection.find(
                {"channel_id": ObjectId(channel_id), "_id": {
                    "$ne": vid_obj_id}}
            ).limit(limit * 2)
            fetch_candidates(chan_cursor, base_score=2)

        # 2. Fetch candidates from text search
        if title:
            search_query = {"$text": {"$search": title},
                            "_id": {"$ne": vid_obj_id}}
            search_cursor = (
                self._collection.find(
                    search_query, {"score": {"$meta": "textScore"}})
                .sort([("score", {"$meta": "textScore"})])
                .limit(limit * 2)
            )
            fetch_candidates(search_cursor, base_score=1, is_text_search=True)

        # 3. Fetch candidates by shared tags
        if tags:
            tag_cursor = self._collection.find(
                {"tags": {"$in": tags}, "_id": {"$ne": vid_obj_id}}
            ).limit(limit * 3)
            fetch_candidates(tag_cursor)

        # 4. Fetch candidates by shared categories
        if categories:
            cat_cursor = self._collection.find(
                {"categories": {"$in": categories}, "_id": {"$ne": vid_obj_id}}
            ).limit(limit * 2)
            fetch_candidates(cat_cursor)

        # 5. Score all gathered candidates
        target_tags = set(t.lower() for t in tags)
        target_cats = set(c.lower() for c in categories)

        for doc in candidates.values():
            # Add points for every matching tag
            doc_tags = doc.get("tags", [])
            for t in doc_tags:
                if t.lower() in target_tags:
                    doc["_relevance_score"] += 3

            # Add points for every matching category
            doc_cats = doc.get("categories", [])
            for c in doc_cats:
                if c.lower() in target_cats:
                    doc["_relevance_score"] += 2

        # 6. Fallback: If we don't have enough candidates, just pad with recent videos
        if len(candidates) < limit:
            recent_cursor = (
                self._collection.find({"_id": {"$ne": vid_obj_id}})
                .sort("created_at", -1)
                .limit(limit)
            )
            for doc in recent_cursor:
                doc_id = str(doc["_id"])
                if doc_id not in candidates:
                    # Negative score ensures they go to the bottom
                    doc["_relevance_score"] = -1
                    candidates[doc_id] = doc
                    if len(candidates) >= limit:
                        break

        # Sort by score descending, then by created_at descending (newest first for ties)
        sorted_candidates = sorted(
            candidates.values(),
            key=lambda x: (x.get("_relevance_score", 0), x.get("created_at")),
            reverse=True
        )

        return sorted_candidates[:limit]

    # ── Update ──────────────────────────────────────────────────────────

    def update_status(
        self,
        id: str,
        status: VideoStatus,
        error_message: str | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> bool:
        """Update the status of a video.

        Args:
            id: MongoDB ObjectId string.
            status: New status value.
            error_message: Error message (for failed status).
            extra_fields: Additional fields to set (e.g. file_path, file_size).

        Returns:
            True if a document was modified.
        """
        update: dict[str, Any] = {
            "status": status,
            "error_message": error_message,
            "updated_at": datetime.now(timezone.utc),
        }
        if extra_fields:
            update.update(extra_fields)

        result: UpdateResult = self._collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update},
        )
        logger.info("video_status_updated", id=id, status=status)
        return result.modified_count > 0

    # ── Delete ──────────────────────────────────────────────────────────

    def delete(self, id: str) -> bool:
        """Delete a video by its MongoDB ObjectId string.

        Returns:
            True if a document was deleted.
        """
        if not ObjectId.is_valid(id):
            return False
        result: DeleteResult = self._collection.delete_one(
            {"_id": ObjectId(id)})
        logger.info("video_deleted", id=id, deleted=result.deleted_count > 0)
        return result.deleted_count > 0

    def count_by_channel(self, channel_id: ObjectId) -> int:
        """Count videos belonging to a channel."""
        return self._collection.count_documents({"channel_id": channel_id})
