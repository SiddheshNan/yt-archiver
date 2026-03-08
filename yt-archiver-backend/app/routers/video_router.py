"""
Video API router.

Endpoints:
    POST   /api/videos          — Submit single video URL
    POST   /api/videos/batch    — Submit multiple URLs
    GET    /api/videos          — List videos (paginated)
    GET    /api/videos/{id}     — Get video details
    DELETE /api/videos/{id}     — Delete video + file
    GET    /api/videos/{id}/stream — Stream video file
    GET    /api/videos/{id}/thumbnail — Serve thumbnail image
    GET    /api/videos/{id}/subtitles/{lang} — Serve subtitle file
"""

from __future__ import annotations
from pydantic import BaseModel

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import FileResponse

from app.database import Database, get_database
from app.schemas.common import PaginatedResponse
from app.schemas.video import (
    AddVideoRequest,
    AddVideoResponse,
    BatchAddVideosRequest,
    BatchAddVideosResponse,
    VideoResponse,
    VideoSummaryResponse,
    VideoCheckResponse,
)
from app.services.video_service import VideoService

router = APIRouter(prefix="/api/videos", tags=["Videos"])


def _get_video_service(db: Database = Depends(get_database)) -> VideoService:
    """Dependency injection for VideoService.

    In production, you'd typically use a proper DI container.
    Here we reconstruct the service per request using the singleton dependencies.
    """
    from app.services.download_manager import get_download_manager
    from app.services.ytdlp_service import get_ytdlp_service
    from app.config import get_settings
    from app.repositories.video_repository import VideoRepository
    from app.repositories.channel_repository import ChannelRepository

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


@router.post(
    "",
    response_model=AddVideoResponse,
    status_code=202,
    summary="Add a video by URL",
    description="Submit a YouTube video URL. The video metadata will be extracted "
                "and the download will be queued in the background.",
)
async def add_video(
    request: AddVideoRequest,
    service: VideoService = Depends(_get_video_service),
) -> AddVideoResponse:
    return await service.add_video(request.url)


@router.get(
    "/check",
    response_model=VideoCheckResponse,
    summary="Check if a video is archived",
    description="Check if a video exists in the database by its YouTube video ID (`v` parameter)",
)
def check_video(
    v: Annotated[str, Query(description="YouTube video ID (e.g., TQqBjSAK52s)")],
    service: VideoService = Depends(_get_video_service),
) -> VideoCheckResponse:
    return service.check_video(v)


@router.post(
    "/batch",
    response_model=BatchAddVideosResponse,
    status_code=202,
    summary="Add multiple videos by URL",
    description="Submit up to 50 YouTube video URLs. Each video is processed "
                "independently — failures don't block other URLs.",
)
async def add_videos_batch(
    request: BatchAddVideosRequest,
    service: VideoService = Depends(_get_video_service),
) -> BatchAddVideosResponse:
    return await service.add_videos_batch(request.urls)


class AddPlaylistRequest(BaseModel):
    url: str


@router.post(
    "/playlist",
    response_model=BatchAddVideosResponse,
    status_code=202,
    summary="Download entire playlist",
    description="Submit a YouTube playlist URL. Extracts all videos and queues them for download.",
)
async def add_playlist(
    request: AddPlaylistRequest,
    service: VideoService = Depends(_get_video_service),
) -> BatchAddVideosResponse:
    return await service.archive_channel(request.url, url_type="playlist")


@router.post(
    "/{video_id}/rearchive",
    response_model=AddVideoResponse,
    status_code=202,
    summary="Re-archive a video",
    description="Check if a previously downloaded video is still available on YouTube. "
                "If it is, delete the old file and re-queue it for download.",
)
async def rearchive_video(
    video_id: str,
    service: VideoService = Depends(_get_video_service),
) -> AddVideoResponse:
    return await service.rearchive_video(video_id)


@router.get(
    "",
    response_model=PaginatedResponse[VideoSummaryResponse],
    summary="List videos",
    description="Paginated list of all videos, newest first.",
)
def list_videos(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: Annotated[str | None, Query(
        description="Filter by status")] = None,
    service: VideoService = Depends(_get_video_service),
) -> PaginatedResponse[VideoSummaryResponse]:
    return service.list_videos(page=page, page_size=page_size, status=status)


# Need a simple schema for exclude_ids request


class HomeRecommendRequest(BaseModel):
    exclude_ids: list[str] = []
    limit: int = 24


@router.post(
    "/recommend/home",
    response_model=list[VideoSummaryResponse],
    summary="Get home page video recommendations",
    description="Returns a random sample of videos. Exclude previously seen IDs to fetch more.",
)
def get_home_recommendations(
    request: HomeRecommendRequest,
    service: VideoService = Depends(_get_video_service),
) -> list[VideoSummaryResponse]:
    return service.get_home_recommendations(
        limit=request.limit, exclude_ids=request.exclude_ids
    )


@router.get(
    "/{video_id}/related",
    response_model=list[VideoSummaryResponse],
    summary="Get related videos",
)
def get_related_videos(
    video_id: str,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    service: VideoService = Depends(_get_video_service),
) -> list[VideoSummaryResponse]:
    return service.get_related_videos(video_id=video_id, limit=limit)


@router.get(
    "/{video_id}",
    response_model=VideoResponse,
    summary="Get video details",
)
def get_video(
    video_id: str,
    service: VideoService = Depends(_get_video_service),
) -> VideoResponse:
    return service.get_video(video_id)


@router.delete(
    "/{video_id}",
    status_code=204,
    summary="Delete a video",
    description="Deletes the video record and removes the file from disk.",
)
def delete_video(
    video_id: str,
    service: VideoService = Depends(_get_video_service),
) -> Response:
    service.delete_video(video_id)
    return Response(status_code=204)


@router.get(
    "/{video_id}/stream",
    summary="Stream video file",
    description="Serves the video file for playback. Returns 404 if the file "
                "hasn't been downloaded yet.",
    responses={
        200: {"content": {"video/mp4": {}}, "description": "Video file stream"},
        404: {"description": "Video or file not found"},
    },
)
def stream_video(
    video_id: str,
    service: VideoService = Depends(_get_video_service),
) -> FileResponse:
    file_path: Path = service.get_video_file_path(video_id)
    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=file_path.name,
    )


@router.get(
    "/{video_id}/thumbnail",
    summary="Get video thumbnail",
    description="Serves the locally stored thumbnail image for the video.",
    responses={
        200: {"content": {"image/*": {}}, "description": "Thumbnail image"},
        404: {"description": "Video or thumbnail not found"},
    },
)
def get_thumbnail(
    video_id: str,
    service: VideoService = Depends(_get_video_service),
) -> FileResponse:
    thumb_path: Path = service.get_thumbnail_path(video_id)
    # Determine media type from extension
    suffix = thumb_path.suffix.lower()
    media_types = {
        ".webp": "image/webp",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }
    media_type = media_types.get(suffix, "image/jpeg")
    return FileResponse(
        path=str(thumb_path),
        media_type=media_type,
        filename=thumb_path.name,
    )


@router.get(
    "/{video_id}/subtitles/{lang}",
    summary="Get video subtitle file",
    description="Serves the locally stored subtitle (.vtt) file for the given language.",
    responses={
        200: {"content": {"text/vtt": {}}, "description": "VTT subtitle file"},
        404: {"description": "Video or subtitle not found"},
    },
)
def get_subtitle(
    video_id: str,
    lang: str,
    service: VideoService = Depends(_get_video_service),
) -> FileResponse:
    sub_path: Path = service.get_subtitle_path(video_id, lang)
    return FileResponse(
        path=str(sub_path),
        media_type="text/vtt",
        filename=sub_path.name,
        headers={"Access-Control-Allow-Origin": "*"},
    )
