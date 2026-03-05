"""
Channel database model.

Defines the document shape for the 'channels' MongoDB collection
and helpers for serialization.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def new_channel_document(
    youtube_channel_id: str,
    name: str,
    description: str | None = None,
    thumbnail_url: str | None = None,
    channel_url: str | None = None,
) -> dict[str, Any]:
    """Create a new channel document ready for insertion.

    Args:
        youtube_channel_id: YouTube's unique channel identifier.
        name: Channel display name.
        description: Channel description (optional).
        thumbnail_url: URL of the channel thumbnail (optional).
        channel_url: YouTube channel page URL (optional).

    Returns:
        Dict suitable for MongoDB insert_one().
    """
    now = datetime.now(timezone.utc)
    return {
        "youtube_channel_id": youtube_channel_id,
        "name": name,
        "description": description,
        "thumbnail_url": thumbnail_url,
        "channel_url": channel_url,
        "video_count": 0,
        "created_at": now,
        "updated_at": now,
    }


def serialize_channel(doc: dict[str, Any]) -> dict[str, Any]:
    """Convert a raw MongoDB channel document to an API-safe dict.

    Converts ObjectId to string and renames _id to id.
    """
    if doc is None:
        return doc
    return {
        "id": str(doc["_id"]),
        "youtube_channel_id": doc["youtube_channel_id"],
        "name": doc["name"],
        "description": doc.get("description"),
        "thumbnail_url": doc.get("thumbnail_url"),
        "channel_url": doc.get("channel_url"),
        "video_count": doc.get("video_count", 0),
        "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
        "updated_at": doc["updated_at"].isoformat() if doc.get("updated_at") else None,
    }
