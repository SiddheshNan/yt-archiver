"""
Channel API router.

Endpoints:
    GET    /api/channels              — List all channels
    GET    /api/channels/{id}         — Channel details
    GET    /api/channels/{id}/videos  — Videos by channel (paginated)
    POST   /api/channels/archive      — Archive entire channel
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.database import Database, get_database
from app.repositories.channel_repository import ChannelRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.channel import ArchiveChannelRequest, ChannelResponse
from app.schemas.common import PaginatedResponse
from app.schemas.video import BatchAddVideosResponse, VideoSummaryResponse
from app.services.channel_service import ChannelService
from app.services.video_service import VideoService

router = APIRouter(prefix="/api/channels", tags=["Channels"])


def _get_channel_service(db: Database = Depends(get_database)) -> ChannelService:
    channel_repo = ChannelRepository(db)
    return ChannelService(channel_repo=channel_repo)


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
    response_model=PaginatedResponse[ChannelResponse],
    summary="List all channels",
)
def list_channels(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    service: ChannelService = Depends(_get_channel_service),
) -> PaginatedResponse[ChannelResponse]:
    return service.list_channels(page=page, page_size=page_size)


@router.get(
    "/{channel_id}",
    response_model=ChannelResponse,
    summary="Get channel details",
)
def get_channel(
    channel_id: str,
    service: ChannelService = Depends(_get_channel_service),
) -> ChannelResponse:
    return service.get_channel(channel_id)


@router.get(
    "/{channel_id}/videos",
    response_model=PaginatedResponse[VideoSummaryResponse],
    summary="List videos by channel",
)
def list_channel_videos(
    channel_id: str,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    service: VideoService = Depends(_get_video_service),
) -> PaginatedResponse[VideoSummaryResponse]:
    return service.list_videos_by_channel(
        channel_id=channel_id, page=page, page_size=page_size
    )


@router.post(
    "/archive",
    response_model=BatchAddVideosResponse,
    status_code=202,
    summary="Archive entire channel",
    description="Submit a YouTube channel or playlist URL. All videos will be "
                "extracted and queued for download.",
)
async def archive_channel(
    request: ArchiveChannelRequest,
    service: VideoService = Depends(_get_video_service),
) -> BatchAddVideosResponse:
    return await service.archive_channel(request.url)


@router.get(
    "/{channel_id}/avatar",
    summary="Get channel avatar URL",
    description="Returns the channel avatar thumbnail URL. "
                "Fetches and caches from YouTube on first call.",
)
async def get_channel_avatar(
    channel_id: str,
    service: ChannelService = Depends(_get_channel_service),
) -> dict:
    from app.services.ytdlp_service import get_ytdlp_service

    channel_repo = service._channel_repo
    doc = channel_repo.find_by_id(channel_id)
    if doc is None:
        from app.exceptions import NotFoundError
        raise NotFoundError("Channel", channel_id)

    # Return cached thumbnail if we've already fetched it
    cached = doc.get("thumbnail_url")
    if cached:
        return {"avatar_url": cached}

    # If we've already attempted a fetch (marked by avatar_fetched flag), don't retry
    if doc.get("avatar_fetched"):
        return {"avatar_url": None}

    # Lazy fetch: use channel_url to extract avatar
    channel_url = doc.get("channel_url")
    if not channel_url:
        yt_id = doc.get("youtube_channel_id", "")
        channel_url = f"https://www.youtube.com/channel/{yt_id}"

    ytdlp = get_ytdlp_service()
    avatar_url = await ytdlp.extract_channel_avatar_url(channel_url)

    # Cache result in DB
    channel_repo.update(
        channel_id,
        {"thumbnail_url": avatar_url or None, "avatar_fetched": True},
    )
    return {"avatar_url": avatar_url}
