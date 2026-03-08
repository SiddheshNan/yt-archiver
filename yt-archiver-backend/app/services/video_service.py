"""
Video service — orchestrates video download lifecycle and CRUD.

This is the primary business logic layer. It coordinates between:
- YtDlpService (metadata extraction)
- DownloadManager (background download queue)
- VideoRepository (data persistence)
- ChannelRepository (auto-creating channels)
"""

from __future__ import annotations

import asyncio
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from bson import ObjectId

from app.config import AppSettings
from app.exceptions import DuplicateError, NotFoundError, ValidationError, ToolError
from app.logging_config import get_logger
from app.models.channel import new_channel_document
from app.models.video import (
    STATUS_PENDING,
    STATUS_FAILED,
    VideoStatus,
    new_video_document,
    serialize_video,
)
from app.repositories.channel_repository import ChannelRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.common import PaginatedResponse
from app.schemas.video import (
    AddVideoResponse,
    BatchAddVideosResponse,
    VideoResponse,
    VideoSummaryResponse,
    VideoCheckResponse,
)
from app.services.download_manager import DownloadJob, DownloadManager
from app.services.ytdlp_service import YtDlpService, extract_video_id_from_url
from app.utils.url_sanitizer import clean_video_url, clean_channel_url, clean_playlist_url

logger = get_logger(__name__)


def _sanitize_dirname(name: str) -> str:
    """Sanitize a string for use as a directory name.

    Replaces unsafe characters with underscores and strips whitespace.
    """
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.strip(". ")
    return name or "unknown_channel"


class VideoService:
    """Business logic for video lifecycle management."""

    def __init__(
        self,
        settings: AppSettings,
        video_repo: VideoRepository,
        channel_repo: ChannelRepository,
        ytdlp_service: YtDlpService,
        download_manager: DownloadManager,
    ) -> None:
        self._settings = settings
        self._video_repo = video_repo
        self._channel_repo = channel_repo
        self._ytdlp = ytdlp_service
        self._download_manager = download_manager
        self._videos_dir = settings.storage.get_videos_path()
        self._metadata_semaphore = asyncio.Semaphore(3)

    # ── Add Video ───────────────────────────────────────────────────────

    async def add_video(self, url: str) -> AddVideoResponse:
        """Submit a single video URL for download asynchronously.

        Flow:
        1. Extract video ID instantly using local regex
        2. Check for duplicates
        3. Create placeholder pending video record
        4. Spawn _process_video_background to fetch metadata and enqueue download
        5. Return 202 Accepted instantly

        Args:
            url: YouTube video URL.
        """
        url = clean_video_url(url)
        logger.info("add_video_sanitized", url=url)

        video_id = extract_video_id_from_url(url)
        if not video_id:
            raise ValidationError(
                "Could not extract video ID from URL locally")

        # Check for duplicates instantly
        existing = self._video_repo.find_by_video_id(video_id)
        if existing:
            raise DuplicateError("Video", video_id)

        # Create placeholder video record so the client gets an ID immediately
        doc = new_video_document(
            video_id=video_id,
            title="Fetching metadata...",
            description="",
            duration=0,
            channel_id=None,
            youtube_channel_id="",
            channel_name="",
            thumbnail_url="",
            upload_date=None,
            view_count=None,
            like_count=None,
            dislike_count=None,
            tags=[],
            categories=[],
        )
        db_id = self._video_repo.create(doc)

        # Spawn background task to do the heavy lifting
        asyncio.create_task(
            self._process_video_background(db_id, video_id, url)
        )

        return AddVideoResponse(
            id=db_id,
            video_id=video_id,
            status=STATUS_PENDING,
            message="Video download queued",
        )

    async def _process_video_background(self, db_id: str, video_id: str, url: str) -> None:
        """Background worker to fetch yt-dlp metadata and enqueue the download."""
        logger.info("background_processing_started", video_id=video_id)
        try:
            # Bound concurrent subprocess and network requests to prevent server crash on large batches
            async with self._metadata_semaphore:
                # Extract metadata
                metadata = await self._ytdlp.extract_metadata(url)

                # Find or create channel
                channel_doc = self._find_or_create_channel(metadata)
                channel_id = channel_doc["_id"]

                # Parse upload date and fetch dislikes
                upload_date = self._parse_upload_date(
                    metadata.get("upload_date"))
                dislikes = await self._fetch_dislikes(video_id)

            channel_name = metadata.get(
                "channel", metadata.get("uploader", "Unknown"))

            # Rich update to the placeholder document
            self._video_repo.update(db_id, {
                "title": metadata.get("title", "Untitled"),
                "description": metadata.get("description", ""),
                "duration": metadata.get("duration", 0),
                "channel_id": channel_id,
                "youtube_channel_id": metadata.get("channel_id", ""),
                "channel_name": channel_name,
                "thumbnail_url": metadata.get("thumbnail", ""),
                "upload_date": upload_date,
                "view_count": metadata.get("view_count"),
                "like_count": metadata.get("like_count"),
                "dislike_count": dislikes,
                "tags": metadata.get("tags", []),
                "categories": metadata.get("categories", []),
            })

            # Increment channel video count
            self._channel_repo.increment_video_count(str(channel_id))

            # Build output directory
            output_dir = self._videos_dir / _sanitize_dirname(channel_name)

            # Enqueue download job
            job = DownloadJob(
                video_db_id=db_id,
                video_id=video_id,
                url=url,
                output_dir=output_dir,
                retries_left=self._settings.downloads.max_retries,
            )
            self._download_manager.enqueue(job)
            logger.info("background_processing_finished", video_id=video_id)

        except Exception as e:
            logger.error("background_processing_failed",
                         video_id=video_id, error=str(e), exc_info=True)
            self._video_repo.update_status(
                db_id,
                STATUS_FAILED,
                error_message=str(e),
                extra_fields={"title": "Unavailable / Private Video"}
            )

    async def add_videos_batch(self, urls: list[str]) -> BatchAddVideosResponse:
        """Submit multiple video URLs for download.

        Each URL is processed independently — failures don't block other URLs.

        Args:
            urls: List of YouTube video URLs.

        Returns:
            BatchAddVideosResponse with queued jobs and any errors.
        """
        queued: list[AddVideoResponse] = []
        errors: list[dict] = []

        for url in urls:
            try:
                result = await self.add_video(url)
                queued.append(result)
            except Exception as e:
                errors.append({"url": url, "error": str(e)})
                logger.warning("batch_add_error", url=url, error=str(e))

        return BatchAddVideosResponse(queued=queued, errors=errors)

    async def archive_channel(self, channel_url: str, url_type: str = "channel") -> BatchAddVideosResponse:
        """Archive all videos from a channel or playlist URL asynchronously.

        Flow:
        1. Sanitize the URL.
        2. Spin up a background task and wait for the flat playlist.
        3. Instantly return a 202 message confirming work has started.

        Args:
            channel_url: YouTube channel or playlist URL.
            url_type: Either "channel" or "playlist".

        Returns:
            BatchAddVideosResponse indicating extraction has begun.
        """
        # Clean URL based on explicit type
        if url_type == "playlist":
            channel_url = clean_playlist_url(channel_url)
        else:
            channel_url = clean_channel_url(channel_url)

        logger.info("archive_channel_sanitized",
                    url=channel_url, url_type=url_type)

        # Dispatch background work
        asyncio.create_task(
            self._process_playlist_background(channel_url)
        )

        return BatchAddVideosResponse(
            message=f"Extraction started for {url_type}. Videos will appear in the queue shortly."
        )

    async def _process_playlist_background(self, channel_url: str) -> None:
        """Background worker to extract playlist URLs and enqueue them with deferred metadata.

        Unlike add_video (which spawns a background metadata task per video),
        this creates skeleton DB entries and enqueues DownloadJob(needs_metadata=True).
        The download worker will fetch metadata + download sequentially, one at a time,
        with cooldown between each — preventing a burst of metadata requests to YouTube.
        """
        logger.info("background_playlist_extraction_started", url=channel_url)
        try:
            # Extract flat playlist (just URLs, no per-video metadata)
            async with self._metadata_semaphore:
                entries = await self._ytdlp.extract_playlist_video_urls(channel_url)

            logger.info("channel_archive_entries",
                        count=len(entries), url=channel_url)

            queued_count = 0
            for entry in entries:
                entry_url = entry.get("url") or entry.get("webpage_url")
                entry_id = entry.get("id")
                if entry_id:
                    entry_url = entry_url or f"https://www.youtube.com/watch?v={entry_id}"
                if entry_url:
                    try:
                        self._add_video_deferred(entry_url)
                        queued_count += 1
                    except (DuplicateError, ValidationError) as e:
                        logger.info("playlist_entry_skipped",
                                    url=entry_url, reason=str(e))

            logger.info("background_playlist_extraction_finished",
                        url=channel_url, queued_count=queued_count)
        except Exception as e:
            logger.error("background_playlist_extraction_failed",
                         url=channel_url, error=str(e), exc_info=True)

    def _add_video_deferred(self, url: str) -> None:
        """Add a video to the download queue WITHOUT fetching metadata upfront.

        Used by the playlist/channel flow. Creates a skeleton DB document
        and enqueues a DownloadJob with needs_metadata=True. The download
        worker will handle metadata extraction + download sequentially.
        """
        url = clean_video_url(url)
        video_id = extract_video_id_from_url(url)
        if not video_id:
            raise ValidationError("Could not extract video ID from URL")

        # Skip duplicates
        existing = self._video_repo.find_by_video_id(video_id)
        if existing:
            raise DuplicateError("Video", video_id)

        # Create a skeleton placeholder (metadata will be filled by the download worker)
        doc = new_video_document(
            video_id=video_id,
            title=f"Queued for download... [{video_id}]",
            description="",
            duration=0,
            channel_id=None,
            youtube_channel_id="",
            channel_name="",
            thumbnail_url="",
            upload_date=None,
            view_count=None,
            like_count=None,
            dislike_count=None,
            tags=[],
            categories=[],
        )
        db_id = self._video_repo.create(doc)

        # Enqueue with deferred metadata — no background task spawned
        job = DownloadJob(
            video_db_id=db_id,
            video_id=video_id,
            url=url,
            needs_metadata=True,
            retries_left=self._settings.downloads.max_retries,
        )
        self._download_manager.enqueue(job)
        logger.info("video_deferred_enqueued", video_id=video_id)

    async def rearchive_video(self, db_id: str) -> AddVideoResponse:
        """Re-archive an existing video.

        1. Wait for yt-dlp to synchronously verify the video is still available.
        2. Delete the old MP4/WebP from disk.
        3. Clear the DB file_path to mark it as undownloaded.
        4. Reset status to pending and enqueue a download job.
        """
        doc = self._video_repo.find_by_id(db_id)
        if not doc:
            raise NotFoundError("Video", db_id)

        video_id = doc["video_id"]
        channel_name = doc.get("channel_name", "Unknown")
        url = f"https://www.youtube.com/watch?v={video_id}"

        logger.info("rearchive_availability_check", video_id=video_id)
        try:
            # We don't use the semaphore here because this is a single, synchronous user-facing request,
            # and we need it to immediately answer 400 if the video is struck by copyright.
            await self._ytdlp.extract_metadata(url)
        except ToolError:
            raise ValidationError(
                "This video is no longer available on YouTube. The current archive will be preserved.")

        # The video is online. We can safely purge our local copies.
        logger.info("rearchive_clearing_old_files", video_id=video_id)

        def _normalize_path(p_str: str) -> Path:
            if "runtime/videos/" in p_str:
                p_str = p_str.split("runtime/videos/")[-1]
            path_obj = Path(p_str)
            if path_obj.is_absolute():
                return path_obj
            return self._videos_dir / p_str

        if doc.get("file_path"):
            path = _normalize_path(doc["file_path"])
            if path.exists():
                path.unlink()

        if doc.get("thumbnail_path"):
            tpath = _normalize_path(doc["thumbnail_path"])
            if tpath.exists():
                tpath.unlink()

        # Update Database to reflect un-downloaded state
        self._video_repo.update(db_id, {
            "status": STATUS_PENDING,
            "file_path": None,
            "file_size": None,
            "thumbnail_path": None,
            "error_message": None,
        })

        # Enqueue Download
        output_dir = self._videos_dir / _sanitize_dirname(channel_name)
        job = DownloadJob(
            video_db_id=db_id,
            video_id=video_id,
            url=url,
            output_dir=output_dir,
            retries_left=self._settings.downloads.max_retries,
        )
        self._download_manager.enqueue(job)
        logger.info("rearchive_job_enqueued", video_id=video_id)

        return AddVideoResponse(
            id=db_id,
            video_id=video_id,
            status=STATUS_PENDING,
            message="Video queued for re-archiving",
        )

    def check_video(self, video_id: str) -> VideoCheckResponse:
        """Check if a video is already archived in the system.

        Args:
            video_id: The YouTube video ID (e.g., TQqBjSAK52s).

        Returns:
            VideoCheckResponse indicating if it's archived and its current status.
        """
        doc = self._video_repo.find_by_video_id(video_id)
        if not doc:
            return VideoCheckResponse(is_archived=False)

        return VideoCheckResponse(
            is_archived=True,
            status=doc.get("status")
        )

    # ── Read ────────────────────────────────────────────────────────────

    def get_video(self, video_id: str) -> VideoResponse:
        """Get detailed video information.

        Args:
            video_id: MongoDB ObjectId string.

        Returns:
            VideoResponse.

        Raises:
            NotFoundError: If video does not exist.
        """
        doc = self._video_repo.find_by_id(video_id)
        if doc is None:
            raise NotFoundError("Video", video_id)
        return VideoResponse(**serialize_video(doc))

    def list_videos(
        self,
        page: int = 1,
        page_size: int = 20,
        status: VideoStatus | None = None,
    ) -> PaginatedResponse[VideoSummaryResponse]:
        """List videos with pagination and optional status filter.

        Args:
            page: Page number (1-indexed).
            page_size: Items per page.
            status: Optional status filter.

        Returns:
            PaginatedResponse containing VideoSummaryResponse items.
        """
        skip = (page - 1) * page_size
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status

        docs, total = self._video_repo.list_paginated(
            skip=skip, limit=page_size, filters=filters
        )
        items = [
            VideoSummaryResponse(**{
                k: serialize_video(doc)[k]
                for k in VideoSummaryResponse.model_fields
            })
            for doc in docs
        ]
        return PaginatedResponse(
            items=items, total=total, page=page, page_size=page_size
        )

    def list_videos_by_channel(
        self,
        channel_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[VideoSummaryResponse]:
        """List videos belonging to a specific channel.

        Args:
            channel_id: MongoDB ObjectId string of the channel.
            page: Page number.
            page_size: Items per page.

        Returns:
            PaginatedResponse containing VideoSummaryResponse items.

        Raises:
            NotFoundError: If channel does not exist.
        """
        # Verify channel exists
        channel = self._channel_repo.find_by_id(channel_id)
        if channel is None:
            raise NotFoundError("Channel", channel_id)

        skip = (page - 1) * page_size
        docs, total = self._video_repo.find_by_channel(
            channel_id=channel_id, skip=skip, limit=page_size
        )
        items = [
            VideoSummaryResponse(**{
                k: serialize_video(doc)[k]
                for k in VideoSummaryResponse.model_fields
            })
            for doc in docs
        ]
        return PaginatedResponse(
            items=items, total=total, page=page, page_size=page_size
        )

    def search_videos(
        self,
        query: str,
        channel_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[VideoSummaryResponse]:
        """Full-text search across videos.

        Args:
            query: Search query text.
            channel_id: Optional channel filter.
            page: Page number.
            page_size: Items per page.

        Returns:
            PaginatedResponse of matching videos.
        """
        skip = (page - 1) * page_size
        docs, total = self._video_repo.search(
            query_text=query,
            channel_id=channel_id,
            skip=skip,
            limit=page_size,
        )
        items = [
            VideoSummaryResponse(**{
                k: serialize_video(doc)[k]
                for k in VideoSummaryResponse.model_fields
            })
            for doc in docs
        ]
        return PaginatedResponse(
            items=items, total=total, page=page, page_size=page_size
        )
    # ── Recommendations ──────────────────────────────────────────────────

    def get_home_recommendations(
        self, limit: int = 24, exclude_ids: list[str] | None = None
    ) -> list[VideoSummaryResponse]:
        """Get random video recommendations for the home page."""
        docs = self._video_repo.get_home_recommendations(
            limit=limit, exclude_ids=exclude_ids or []
        )
        return [
            VideoSummaryResponse(**{
                k: serialize_video(doc)[k]
                for k in VideoSummaryResponse.model_fields
            })
            for doc in docs
        ]

    def get_related_videos(
        self, video_id: str, limit: int = 20
    ) -> list[VideoSummaryResponse]:
        """Get related videos for a given video ID."""
        video = self._video_repo.find_by_id(video_id)
        if not video:
            raise NotFoundError("Video", video_id)

        docs = self._video_repo.get_related_videos(
            current_video_id=video_id,
            channel_id=str(video.get("channel_id", "")),
            title=video.get("title", ""),
            tags=video.get("tags", []),
            categories=video.get("categories", []),
            limit=limit,
        )
        return [
            VideoSummaryResponse(**{
                k: serialize_video(doc)[k]
                for k in VideoSummaryResponse.model_fields
            })
            for doc in docs
        ]
    # ── Delete ──────────────────────────────────────────────────────────

    def delete_video(self, video_id: str) -> None:
        """Delete a video record and its file from disk.

        Args:
            video_id: MongoDB ObjectId string.

        Raises:
            NotFoundError: If video does not exist.
        """
        doc = self._video_repo.find_by_id(video_id)
        if doc is None:
            raise NotFoundError("Video", video_id)

        # Legacy path normalizer to fix old absolute paths stored in DB
        def _normalize_path(p_str: str) -> Path:
            if "runtime/videos/" in p_str:
                p_str = p_str.split("runtime/videos/")[-1]

            # If still absolute (fallback), try to make it relative
            path_obj = Path(p_str)
            if path_obj.is_absolute():
                return path_obj
            return self._videos_dir / p_str

        # Delete video file from disk
        file_path = doc.get("file_path")
        if file_path:
            path = _normalize_path(file_path)
            if path.exists():
                path.unlink()
                logger.info("video_file_deleted", file_path=str(path))

        # Delete thumbnail file from disk
        thumb_path = doc.get("thumbnail_path")
        if thumb_path:
            tpath = _normalize_path(thumb_path)
            if tpath.exists():
                tpath.unlink()
                logger.info("thumbnail_file_deleted",
                            thumbnail_path=str(tpath))

        # Delete subtitle files from disk
        for track in doc.get("subtitle_tracks", []):
            sub_path = track.get("path")
            if sub_path:
                spath = _normalize_path(sub_path)
                if spath.exists():
                    spath.unlink()
                    logger.info("subtitle_file_deleted",
                                subtitle_path=str(spath))

        # Decrement channel video count
        channel_id = doc.get("channel_id")
        if channel_id:
            self._channel_repo.increment_video_count(str(channel_id), delta=-1)

        # Delete from database
        self._video_repo.delete(video_id)
        logger.info("video_deleted", video_id=video_id)

    def get_video_file_path(self, video_id: str) -> Path:
        """Get the file path for a video (for streaming).

        Args:
            video_id: MongoDB ObjectId string.

        Returns:
            Path to the video file.

        Raises:
            NotFoundError: If video or file does not exist.
        """
        doc = self._video_repo.find_by_id(video_id)
        if doc is None:
            raise NotFoundError("Video", video_id)

        file_path = doc.get("file_path")
        if not file_path:
            raise NotFoundError("Video file", video_id)

        if "runtime/videos/" in file_path:
            file_path = file_path.split("runtime/videos/")[-1]

        path = Path(file_path)
        if not path.is_absolute():
            path = self._videos_dir / path

        if not path.exists():
            raise NotFoundError("Video file", str(path))

        return path

    def get_thumbnail_path(self, video_id: str) -> Path:
        """Get the local thumbnail file path for a video.

        Args:
            video_id: MongoDB ObjectId string.

        Returns:
            Path to the thumbnail file.

        Raises:
            NotFoundError: If video or thumbnail file does not exist.
        """
        doc = self._video_repo.find_by_id(video_id)
        if doc is None:
            raise NotFoundError("Video", video_id)

        thumb_path = doc.get("thumbnail_path")
        if not thumb_path:
            raise NotFoundError("Video thumbnail", video_id)

        if "runtime/videos/" in thumb_path:
            thumb_path = thumb_path.split("runtime/videos/")[-1]

        path = Path(thumb_path)
        if not path.is_absolute():
            path = self._videos_dir / path

        if not path.exists():
            raise NotFoundError("Video thumbnail", str(path))

        return path

    def get_subtitle_path(self, video_id: str, lang: str) -> Path:
        """Get the local subtitle file path for a video by language code.

        Args:
            video_id: MongoDB ObjectId string.
            lang: Language code (e.g. 'en', 'en-orig').

        Returns:
            Path to the .vtt subtitle file.

        Raises:
            NotFoundError: If video, subtitle track, or file does not exist.
        """
        doc = self._video_repo.find_by_id(video_id)
        if doc is None:
            raise NotFoundError("Video", video_id)

        tracks = doc.get("subtitle_tracks", [])
        track = next((t for t in tracks if t.get("lang") == lang), None)
        if not track:
            raise NotFoundError("Subtitle track", f"{video_id}/{lang}")

        sub_path = track.get("path", "")
        if not sub_path:
            raise NotFoundError("Subtitle file", f"{video_id}/{lang}")

        path = Path(sub_path)
        if not path.is_absolute():
            path = self._videos_dir / path

        if not path.exists():
            raise NotFoundError("Subtitle file", str(path))

        return path

    # ── Private helpers ─────────────────────────────────────────────────

    def _find_or_create_channel(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Find an existing channel or create a new one from video metadata.

        Args:
            metadata: yt-dlp video metadata dict.

        Returns:
            Channel document (existing or newly created).
        """
        yt_channel_id = metadata.get("channel_id", "")
        if not yt_channel_id:
            # Fallback: use uploader_id
            yt_channel_id = metadata.get("uploader_id", "unknown")

        existing = self._channel_repo.find_by_youtube_id(yt_channel_id)
        if existing:
            return existing

        doc = new_channel_document(
            youtube_channel_id=yt_channel_id,
            name=metadata.get("channel", metadata.get("uploader", "Unknown")),
            description=metadata.get("channel_description"),
            thumbnail_url=metadata.get("channel_thumbnail"),
            channel_url=metadata.get(
                "channel_url") or metadata.get("uploader_url"),
        )
        channel_id = self._channel_repo.create(doc)

        # Re-fetch to get the full document with _id
        return self._channel_repo.find_by_id(channel_id)

    @staticmethod
    def _parse_upload_date(date_str: str | None) -> datetime | None:
        """Parse yt-dlp upload_date format (YYYYMMDD) to datetime."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    @staticmethod
    async def _fetch_dislikes(video_id: str) -> int | None:
        """Safe non-blocking wrapper to fetch dislike count from Return YouTube Dislike API."""
        def _get() -> int | None:
            try:
                # 5 second timeout so we never block downloads if the third-party API is down.
                resp = requests.get(
                    f"https://returnyoutubedislikeapi.com/votes?videoId={video_id}",
                    timeout=5,
                    headers={"User-Agent": "Mozilla/5.0 yt-archiver"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("dislikes")
            except Exception as e:
                logger.warning("ryd_api_error",
                               video_id=video_id, error=str(e))
            return None

        return await asyncio.to_thread(_get)
