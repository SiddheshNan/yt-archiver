"""
Search API router.

Endpoints:
    GET /api/search — Full-text search across videos
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.database import Database, get_database
from app.repositories.channel_repository import ChannelRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.common import PaginatedResponse
from app.schemas.video import VideoSummaryResponse
from app.services.video_service import VideoService

router = APIRouter(prefix="/api/search", tags=["Search"])


def _get_video_service(db: Database = Depends(get_database)) -> VideoService:
    from app.config import get_settings
    from app.services.download_manager import get_download_manager
    from app.services.ytdlp_service import get_ytdlp_service

    settings = get_settings()
    video_repo = VideoRepository(db)
    channel_repo = ChannelRepository(db)
    ytdlp_service = get_ytdlp_service()
    download_manager = get_download_manager()

    return VideoService(
        settings=settings,
        video_repo=video_repo,
        channel_repo=channel_repo,
        ytdlp_service=ytdlp_service,
        download_manager=download_manager,
    )


@router.get(
    "",
    response_model=PaginatedResponse[VideoSummaryResponse],
    summary="Search videos",
    description="Full-text search across video title, description, and channel name. "
                "Optionally filter by channel.",
)
def search_videos(
    q: Annotated[str, Query(min_length=1, max_length=200, description="Search query")],
    channel_id: Annotated[str | None, Query(
        description="Filter by channel ID")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    service: VideoService = Depends(_get_video_service),
) -> PaginatedResponse[VideoSummaryResponse]:
    return service.search_videos(
        query=q, channel_id=channel_id, page=page, page_size=page_size
    )
