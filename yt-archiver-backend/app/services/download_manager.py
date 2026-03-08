"""
Download manager — asyncio-based background download queue.

Spawns a configurable number of worker tasks that pull download
jobs from an asyncio.Queue and process them sequentially/concurrently.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from app.config import AppSettings
from app.logging_config import get_logger
from app.models.channel import new_channel_document
from app.models.video import STATUS_COMPLETED, STATUS_DOWNLOADING, STATUS_FAILED
from app.repositories.channel_repository import ChannelRepository
from app.repositories.video_repository import VideoRepository
from app.services.ytdlp_service import YtDlpService

logger = get_logger(__name__)


def _sanitize_dirname(name: str) -> str:
    """Sanitize a string for use as a directory name."""
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.strip(". ")
    return name or "unknown_channel"


@dataclass
class DownloadJob:
    """Represents a single video download job."""

    video_db_id: str          # MongoDB ObjectId string
    video_id: str             # YouTube video ID
    url: str                  # Full YouTube URL
    # Target directory (resolved after metadata for deferred jobs)
    output_dir: Path | None = None
    retries_left: int = 0
    needs_metadata: bool = False  # If True, fetch metadata before downloading
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc))


class DownloadManager:
    """Manages an asyncio.Queue of download jobs with worker tasks.

    Usage:
        manager = DownloadManager(settings, video_repo, channel_repo, ytdlp_service)
        await manager.start()       # call during app startup
        manager.enqueue(job)        # add jobs from API handlers
        await manager.stop()        # call during app shutdown
    """

    def __init__(
        self,
        settings: AppSettings,
        video_repo: VideoRepository,
        channel_repo: ChannelRepository,
        ytdlp_service: YtDlpService,
    ) -> None:
        self._settings = settings
        self._video_repo = video_repo
        self._channel_repo = channel_repo
        self._ytdlp = ytdlp_service
        self._queue: asyncio.Queue[DownloadJob] = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._running = False

    async def start(self) -> None:
        """Start the download worker tasks."""
        if self._running:
            return
        self._running = True
        max_workers = self._settings.downloads.max_concurrent
        logger.info("download_manager_starting", workers=max_workers)

        for i in range(max_workers):
            task = asyncio.create_task(
                self._worker(f"worker-{i}"), name=f"download-worker-{i}"
            )
            self._workers.append(task)

    async def stop(self) -> None:
        """Gracefully stop all worker tasks.

        Waits for currently processing jobs to finish, then cancels workers.
        """
        if not self._running:
            return
        self._running = False
        logger.info("download_manager_stopping")

        # Cancel all workers
        for task in self._workers:
            task.cancel()

        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("download_manager_stopped")

    def enqueue(self, job: DownloadJob) -> None:
        """Add a download job to the queue.

        This is a synchronous call — safe to call from sync FastAPI route handlers.
        """
        self._queue.put_nowait(job)
        logger.info(
            "job_enqueued",
            video_id=job.video_id,
            queue_size=self._queue.qsize(),
        )

    @property
    def queue_size(self) -> int:
        """Current number of jobs waiting in the queue."""
        return self._queue.qsize()

    @property
    def active_workers(self) -> int:
        """Number of worker tasks currently running."""
        return len([w for w in self._workers if not w.done()])

    def get_status(self) -> dict[str, Any]:
        """Return a snapshot of the queue status."""
        return {
            "queue_size": self.queue_size,
            "active_workers": self.active_workers,
            "max_workers": self._settings.downloads.max_concurrent,
            "running": self._running,
        }

    # ── Worker logic ────────────────────────────────────────────────────

    async def _worker(self, name: str) -> None:
        """Worker loop: pull jobs from queue and process them."""
        logger.info("worker_started", worker=name)
        try:
            while self._running:
                try:
                    job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                try:
                    await self._process_job(job, name)
                except Exception as e:
                    logger.error(
                        "worker_job_error",
                        worker=name,
                        video_id=job.video_id,
                        error=str(e),
                        exc_info=True,
                    )
                finally:
                    self._queue.task_done()
                    # Cooldown between downloads to avoid YouTube rate-limiting
                    cooldown = self._settings.downloads.cooldown_seconds
                    if cooldown > 0:
                        await asyncio.sleep(cooldown)
        except asyncio.CancelledError:
            logger.info("worker_cancelled", worker=name)

    async def _process_job(self, job: DownloadJob, worker_name: str) -> None:
        """Process a single download job."""
        logger.info(
            "processing_download",
            worker=worker_name,
            video_id=job.video_id,
            db_id=job.video_db_id,
        )

        # Verify the video hasn't been deleted by the user while waiting in the queue
        doc = self._video_repo.find_by_id(job.video_db_id)
        if not doc:
            logger.info("download_cancelled_video_deleted",
                        video_id=job.video_id)
            return

        # If the job needs metadata, fetch it first before downloading
        if job.needs_metadata:
            success = await self._fetch_metadata_and_enrich(job)
            if not success:
                return  # Video is unavailable/private — already marked failed

        # Mark as downloading
        self._video_repo.update_status(job.video_db_id, STATUS_DOWNLOADING)

        try:
            file_path = await self._ytdlp.download_video(
                url=job.url,
                output_dir=job.output_dir,
            )

            # Get file size
            file_size = file_path.stat().st_size if file_path.exists() else None

            # Find thumbnail written by --write-thumbnail
            thumbnail_path = self._find_thumbnail(file_path)

            # Find subtitle files written by --write-subs / --write-auto-subs
            subtitle_tracks = self._find_subtitle_files(file_path)

            # Make paths relative to videos_dir for portable storage
            videos_dir = self._settings.storage.get_videos_path()
            try:
                rel_file_path = str(file_path.relative_to(videos_dir))
            except ValueError:
                rel_file_path = str(file_path)

            extra: dict[str, Any] = {
                "file_path": rel_file_path,
                "file_size": file_size,
            }
            if thumbnail_path:
                try:
                    rel_thumb_path = str(
                        thumbnail_path.relative_to(videos_dir))
                except ValueError:
                    rel_thumb_path = str(thumbnail_path)
                extra["thumbnail_path"] = rel_thumb_path

            # Store subtitle tracks with relative paths
            if subtitle_tracks:
                for track in subtitle_tracks:
                    try:
                        track["path"] = str(
                            Path(track["path"]).relative_to(videos_dir))
                    except ValueError:
                        pass  # keep absolute path as fallback
                extra["subtitle_tracks"] = subtitle_tracks

            self._video_repo.update_status(
                job.video_db_id,
                STATUS_COMPLETED,
                extra_fields=extra,
            )
            logger.info(
                "download_completed",
                video_id=job.video_id,
                file_path=str(file_path),
                file_size=file_size,
                thumbnail_path=str(thumbnail_path) if thumbnail_path else None,
                subtitle_count=len(subtitle_tracks),
            )

        except Exception as e:
            error_msg = str(e)

            # Retry logic
            if job.retries_left > 0:
                job.retries_left -= 1
                logger.warning(
                    "download_retrying",
                    video_id=job.video_id,
                    retries_left=job.retries_left,
                    error=error_msg,
                )
                self.enqueue(job)
                return

            # Mark as failed
            self._video_repo.update_status(
                job.video_db_id,
                STATUS_FAILED,
                error_message=error_msg,
            )
            logger.error(
                "download_failed",
                video_id=job.video_id,
                error=error_msg,
            )

    async def _fetch_metadata_and_enrich(self, job: DownloadJob) -> bool:
        """Fetch metadata for a deferred job and update the DB record.

        Called by _process_job when job.needs_metadata is True.
        This is the playlist/channel path where metadata was not fetched upfront.

        Returns:
            True if metadata was fetched successfully and download should proceed.
            False if the video is unavailable (already marked as failed in DB).
        """
        logger.info("deferred_metadata_fetch_started", video_id=job.video_id)
        try:
            metadata = await self._ytdlp.extract_metadata(job.url)
        except Exception as e:
            logger.error("deferred_metadata_fetch_failed",
                         video_id=job.video_id, error=str(e))
            self._video_repo.update_status(
                job.video_db_id,
                STATUS_FAILED,
                error_message=str(e),
                extra_fields={"title": "Unavailable / Private Video"},
            )
            return False

        # Find or create channel
        channel_doc = self._find_or_create_channel(metadata)
        channel_id = channel_doc["_id"]

        # Parse upload date
        upload_date = self._parse_upload_date(metadata.get("upload_date"))

        # Fetch dislikes (non-blocking, safe to fail)
        dislikes = await self._fetch_dislikes(job.video_id)

        channel_name = metadata.get(
            "channel", metadata.get("uploader", "Unknown"))

        # Update the placeholder document with real metadata
        self._video_repo.update(job.video_db_id, {
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

        # Resolve the output directory now that we know the channel name
        videos_dir = self._settings.storage.get_videos_path()
        job.output_dir = videos_dir / _sanitize_dirname(channel_name)

        logger.info("deferred_metadata_fetch_finished", video_id=job.video_id,
                    title=metadata.get("title"))
        return True

    def _find_or_create_channel(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Find an existing channel or create a new one from video metadata."""
        yt_channel_id = metadata.get("channel_id", "")
        if not yt_channel_id:
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
        """Safe non-blocking wrapper to fetch dislike count."""
        def _get() -> int | None:
            try:
                resp = requests.get(
                    f"https://returnyoutubedislikeapi.com/votes?videoId={video_id}",
                    timeout=5,
                    headers={"User-Agent": "Mozilla/5.0 yt-archiver"},
                )
                if resp.status_code == 200:
                    return resp.json().get("dislikes")
            except Exception as e:
                logger.warning("ryd_api_error",
                               video_id=video_id, error=str(e))
            return None

        return await asyncio.to_thread(_get)

    @staticmethod
    def _find_thumbnail(video_path: Path) -> Path | None:
        """Find the thumbnail file alongside a downloaded video.

        yt-dlp --write-thumbnail saves thumbnails with the same stem
        as the video but with image extensions (webp, jpg, png).
        """
        stem = video_path.stem
        parent = video_path.parent
        for ext in (".webp", ".jpg", ".jpeg", ".png"):
            candidate = parent / f"{stem}{ext}"
            if candidate.exists():
                return candidate
        return None

    @staticmethod
    def _find_subtitle_files(video_path: Path) -> list[dict[str, str]]:
        """Find subtitle (.vtt) files alongside a downloaded video.

        yt-dlp names subtitle files as: VideoTitle [id].lang.vtt
        For auto-generated subs: VideoTitle [id].lang-orig.vtt (sometimes with complex suffixes)

        Note: We can't use glob() here because the video stem contains
        square brackets (e.g. [9HDEHj2yzew]) which glob interprets as
        character class patterns, causing matches to silently fail.

        Returns:
            List of dicts with 'lang', 'label', and 'path' keys.
        """
        stem = video_path.stem
        parent = video_path.parent
        prefix = f"{stem}."
        tracks: list[dict[str, str]] = []

        try:
            for entry in parent.iterdir():
                if not entry.is_file():
                    continue
                if not entry.name.startswith(prefix):
                    continue
                if not entry.name.endswith(".vtt"):
                    continue

                # Extract the language code from the filename
                # e.g. "Video Title [abc123].en.vtt" -> "en"
                suffix_part = entry.name[len(prefix):]  # "en.vtt"
                lang_code = suffix_part.rsplit(".vtt", 1)[0]  # "en"

                if not lang_code:
                    continue

                # Build human-readable label
                label = lang_code.upper()
                if "-orig" in lang_code:
                    # Auto-generated subtitles from yt-dlp
                    base_lang = lang_code.split("-orig")[0]
                    label = f"{base_lang.upper()} (auto)"

                tracks.append({
                    "lang": lang_code,
                    "label": label,
                    "path": str(entry),
                })
        except OSError as e:
            logger.warning("subtitle_scan_error", error=str(e))

        # Sort: manual subs first, auto subs last
        tracks.sort(key=lambda t: (
            1 if "auto" in t["label"] else 0, t["lang"]))
        logger.info("subtitle_files_found", count=len(tracks),
                    langs=[t["lang"] for t in tracks])
        return tracks


# ---------------------------------------------------------------------------
# Singleton access
# ---------------------------------------------------------------------------

_download_manager: DownloadManager | None = None


def init_download_manager(
    settings: AppSettings,
    video_repo: VideoRepository,
    channel_repo: ChannelRepository,
    ytdlp_service: YtDlpService,
) -> DownloadManager:
    """Initialize the global DownloadManager singleton."""
    global _download_manager
    _download_manager = DownloadManager(
        settings, video_repo, channel_repo, ytdlp_service)
    return _download_manager


def get_download_manager() -> DownloadManager:
    """Return the cached DownloadManager. Raises if not initialized."""
    if _download_manager is None:
        raise RuntimeError("DownloadManager not initialized.")
    return _download_manager
