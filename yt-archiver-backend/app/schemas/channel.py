"""
Channel API schemas — request and response models.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChannelResponse(BaseModel):
    """Single channel in API responses."""

    id: str
    youtube_channel_id: str
    name: str
    description: str | None
    thumbnail_url: str | None
    channel_url: str | None
    video_count: int
    created_at: str | None
    updated_at: str | None


class ArchiveChannelRequest(BaseModel):
    """Request body for POST /api/channels/archive."""

    url: str = Field(
        ...,
        description="YouTube channel or playlist URL",
        examples=["https://www.youtube.com/@channelname"],
    )
