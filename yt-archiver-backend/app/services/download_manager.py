"""
Download manager — asyncio-based background download queue.

Spawns a configurable number of worker tasks that pull download
jobs from an asyncio.Queue and process them sequentially/concurrently.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import AppSettings
from app.logging_config import get_logger
from app.models.video import STATUS_COMPLETED, STATUS_DOWNLOADING, STATUS_FAILED
from app.repositories.channel_repository import ChannelRepository
from app.repositories.video_repository import VideoRepository
from app.services.ytdlp_service import YtDlpService

logger = get_logger(__name__)


@dataclass
class DownloadJob:
    """Represents a single video download job."""

    video_db_id: str          # MongoDB ObjectId string
    video_id: str             # YouTube video ID
    url: str                  # Full YouTube URL
    output_dir: Path          # Target directory for the downloaded file
    retries_left: int = 0
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
