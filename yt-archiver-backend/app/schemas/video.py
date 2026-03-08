"""
Video API schemas — request and response models.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class AddVideoRequest(BaseModel):
    """Request body for POST /api/videos."""

    url: str = Field(
        ...,
        description="YouTube video URL",
        examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
    )


class BatchAddVideosRequest(BaseModel):
    """Request body for POST /api/videos/batch."""

    urls: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of YouTube video URLs (max 50)",
    )


class VideoResponse(BaseModel):
    """Single video in API responses."""

    id: str
    video_id: str
    title: str
    description: str
    duration: int
    channel_id: str | None
    youtube_channel_id: str
    channel_name: str
    thumbnail_url: str
    thumbnail_path: str | None
    upload_date: str | None
    view_count: int | None
    like_count: int | None
    dislike_count: int | None
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    file_path: str | None
    file_size: int | None
    subtitle_tracks: list[dict] = Field(default_factory=list)
    status: str
    error_message: str | None
    created_at: str | None
    updated_at: str | None


class VideoSummaryResponse(BaseModel):
    """Lightweight video representation for list views.

    Omits description and file_path to reduce payload size.
    """

    id: str
    video_id: str
    title: str
    duration: int
    channel_id: str | None
    channel_name: str
    thumbnail_url: str
    thumbnail_path: str | None
    upload_date: str | None
    view_count: int | None
    like_count: int | None
    dislike_count: int | None
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    status: str
    created_at: str | None


class AddVideoResponse(BaseModel):
    """Response body for POST /api/videos — confirms the job was queued."""

    id: str
    video_id: str
    status: str
    message: str = "Video download queued"


class BatchAddVideosResponse(BaseModel):
    """Response body for POST /api/videos/batch."""

    message: str | None = None
    queued: list[AddVideoResponse] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)


class VideoCheckResponse(BaseModel):
    """Response body for GET /api/videos/check?v=<id>."""

    is_archived: bool
    status: str | None = None
