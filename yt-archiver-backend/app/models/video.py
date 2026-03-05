"""
Video database model.

Defines the document shape for the 'videos' MongoDB collection,
status constants, and serialization helpers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from bson import ObjectId

# Video status constants
STATUS_PENDING = "pending"
STATUS_DOWNLOADING = "downloading"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

VideoStatus = Literal["pending", "downloading", "completed", "failed"]


def new_video_document(
    video_id: str,
    title: str,
    description: str,
    duration: int,
    channel_id: ObjectId,
    youtube_channel_id: str,
    channel_name: str,
    thumbnail_url: str,
    upload_date: datetime | None = None,
    view_count: int | None = None,
    like_count: int | None = None,
    dislike_count: int | None = None,
    tags: list[str] | None = None,
    categories: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new video document ready for insertion.

    Args:
        video_id: YouTube video ID (e.g. "dQw4w9WgXcQ").
        title: Video title.
        description: Video description.
        duration: Duration in seconds.
        channel_id: MongoDB ObjectId reference to the channels collection.
        youtube_channel_id: YouTube's channel ID.
        channel_name: Denormalized channel name for text search.
        thumbnail_url: URL of the video thumbnail.
        upload_date: Original upload date on YouTube.
        view_count: YouTube view count at time of download (reference only).
        like_count: YouTube like count.
        dislike_count: YouTube dislike count (via Return YouTube Dislike API).

    Returns:
        Dict suitable for MongoDB insert_one().
    """
    now = datetime.now(timezone.utc)
    return {
        "video_id": video_id,
        "title": title,
        "description": description,
        "duration": duration,
        "channel_id": channel_id,
        "youtube_channel_id": youtube_channel_id,
        "channel_name": channel_name,
        "thumbnail_url": thumbnail_url,
        "upload_date": upload_date,
        "view_count": view_count,
        "like_count": like_count,
        "dislike_count": dislike_count,
        "tags": tags or [],
        "categories": categories or [],
        "file_path": None,
        "file_size": None,
        "thumbnail_path": None,
        "status": STATUS_PENDING,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }


def serialize_video(doc: dict[str, Any]) -> dict[str, Any]:
    """Convert a raw MongoDB video document to an API-safe dict.

    Converts ObjectId fields to strings, renames _id to id,
    and formats datetime fields as ISO strings.
    """
    if doc is None:
        return doc

    def _fmt_dt(val: Any) -> str | None:
        if isinstance(val, datetime):
            return val.isoformat()
        return val

    return {
        "id": str(doc["_id"]),
        "video_id": doc["video_id"],
        "title": doc["title"],
        "description": doc.get("description", ""),
        "duration": doc.get("duration", 0),
        "channel_id": str(doc["channel_id"]) if doc.get("channel_id") else None,
        "youtube_channel_id": doc.get("youtube_channel_id", ""),
        "channel_name": doc.get("channel_name", ""),
        "thumbnail_url": doc.get("thumbnail_url", ""),
        "upload_date": _fmt_dt(doc.get("upload_date")),
        "view_count": doc.get("view_count"),
        "like_count": doc.get("like_count"),
        "dislike_count": doc.get("dislike_count"),
        "tags": doc.get("tags", []),
        "categories": doc.get("categories", []),
        "file_path": doc.get("file_path"),
        "file_size": doc.get("file_size"),
        "thumbnail_path": doc.get("thumbnail_path"),
        "status": doc.get("status", STATUS_PENDING),
        "error_message": doc.get("error_message"),
        "created_at": _fmt_dt(doc.get("created_at")),
        "updated_at": _fmt_dt(doc.get("updated_at")),
    }
