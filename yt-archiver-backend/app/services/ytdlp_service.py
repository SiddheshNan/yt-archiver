"""
yt-dlp service — wraps the yt-dlp and ffmpeg external binaries.

All external tool invocations go through this service. Uses
asyncio subprocesses for non-blocking execution.
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

from app.config import AppSettings
from app.exceptions import ToolError
from app.logging_config import get_logger

logger = get_logger(__name__)

# Regex to extract YouTube video ID from various URL formats
_YT_VIDEO_REGEX = re.compile(
    r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|v/|shorts/))([a-zA-Z0-9_-]{11})"
)


def extract_video_id_from_url(url: str) -> str | None:
    """Extract the YouTube video ID from a URL.

    Supports youtube.com/watch, youtu.be, /embed/, /v/, /shorts/ formats.

    Returns:
        The 11-character video ID, or None if not found.
    """
    match = _YT_VIDEO_REGEX.search(url)
    return match.group(1) if match else None


class YtDlpService:
    """Wraps yt-dlp and ffmpeg as async subprocesses."""

    def __init__(self, settings: AppSettings) -> None:
        self._ytdlp = str(settings.tools.get_ytdlp_path())
        self._ffmpeg_dir = str(settings.tools.get_ffmpeg_path().parent)
        self._ffmpeg = str(settings.tools.get_ffmpeg_path())
        self._timeout = settings.downloads.timeout
        self._retries = str(settings.downloads.retries)
        self._cookies_file = settings.downloads.get_cookies_file_path()
        self._browser_cookies = settings.downloads.browser_cookies

    def _append_cookie_args(self, cmd: list[str]) -> None:
        """Inject cookie arguments into the yt-dlp command list before the URL."""
        # The URL is always the last element in the cmd list
        if self._cookies_file and self._cookies_file.exists():
            cmd.insert(-1, "--cookies")
            cmd.insert(-1, str(self._cookies_file))
        elif self._browser_cookies:
            cmd.insert(-1, "--cookies-from-browser")
            cmd.insert(-1, self._browser_cookies)

    async def extract_metadata(self, url: str) -> dict[str, Any]:
        """Extract video metadata without downloading.

        Runs: yt-dlp --dump-json --no-download <url>

        Returns:
            Parsed JSON metadata dict from yt-dlp.

        Raises:
            ToolError: If yt-dlp fails or returns invalid JSON.
        """
        logger.info("extracting_metadata", url=url)
        cmd = [
            self._ytdlp,
            "--dump-json",
            "--no-download",
            "--no-warnings",
            "--js-runtimes", "node",
            "--ffmpeg-location", self._ffmpeg_dir,
            url,
        ]
        self._append_cookie_args(cmd)
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=120
            )
        except asyncio.TimeoutError:
            raise ToolError("yt-dlp", "Metadata extraction timed out")
        except FileNotFoundError:
            raise ToolError("yt-dlp", f"Binary not found at {self._ytdlp}")

        if proc.returncode != 0:
            err_msg = stderr.decode(errors="replace").strip()
            logger.error("ytdlp_metadata_failed", stderr=err_msg)
            raise ToolError("yt-dlp", f"Metadata extraction failed: {err_msg}")

        try:
            return json.loads(stdout.decode())
        except json.JSONDecodeError as e:
            raise ToolError("yt-dlp", f"Invalid JSON output: {e}")

    async def extract_playlist_video_urls(self, url: str) -> list[dict[str, Any]]:
        """Extract video entries from a channel or playlist URL.

        Runs: yt-dlp --flat-playlist --dump-json <url>

        Returns:
            List of dicts with at least 'id', 'title', 'url' keys.

        Raises:
            ToolError: If yt-dlp fails.
        """
        logger.info("extracting_playlist", url=url)
        cmd = [
            self._ytdlp,
            "--flat-playlist",
            "--dump-json",
            "--no-warnings",
            "--js-runtimes", "node",
            url,
        ]
        self._append_cookie_args(cmd)
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=300
            )
        except asyncio.TimeoutError:
            raise ToolError("yt-dlp", "Playlist extraction timed out")
        except FileNotFoundError:
            raise ToolError("yt-dlp", f"Binary not found at {self._ytdlp}")

        if proc.returncode != 0:
            err_msg = stderr.decode(errors="replace").strip()
            raise ToolError("yt-dlp", f"Playlist extraction failed: {err_msg}")

        entries = []
        for line in stdout.decode().strip().splitlines():
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries

    async def download_video(
        self,
        url: str,
        output_dir: Path,
        filename_template: str = "%(title)s [%(id)s].%(ext)s",
    ) -> Path:
        """Download a video to the specified directory.

        Runs: yt-dlp -f bestvideo+bestaudio/best --merge-output-format mp4 -o <template> <url>

        Args:
            url: YouTube video URL.
            output_dir: Directory to save the video file.
            filename_template: yt-dlp output template for the filename.

        Returns:
            Path to the downloaded video file.

        Raises:
            ToolError: If the download fails.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        output_template = str(output_dir / filename_template)

        logger.info("downloading_video", url=url, output_dir=str(output_dir))
        cmd = [
            self._ytdlp,
            "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best",
            "--merge-output-format", "mp4",
            "--ffmpeg-location", self._ffmpeg_dir,
            "--no-warnings",
            "--js-runtimes", "node",
            "--no-playlist",
            "--write-thumbnail",
            "--retries", self._retries,
            "--fragment-retries", self._retries,
            "-o", output_template,
            "--print", "after_move:filepath",
            url,
        ]
        self._append_cookie_args(cmd)
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self._timeout
            )
        except asyncio.TimeoutError:
            raise ToolError(
                "yt-dlp", f"Download timed out after {self._timeout}s")
        except FileNotFoundError:
            raise ToolError("yt-dlp", f"Binary not found at {self._ytdlp}")

        if proc.returncode != 0:
            err_msg = stderr.decode(errors="replace").strip()
            logger.error("ytdlp_download_failed", stderr=err_msg)
            raise ToolError("yt-dlp", f"Download failed: {err_msg}")

        # The --print flag outputs the final file path
        file_path_str = stdout.decode().strip().splitlines()[-1]
        file_path = Path(file_path_str)

        if not file_path.exists():
            raise ToolError(
                "yt-dlp", f"Downloaded file not found: {file_path}")

        logger.info("download_complete", file_path=str(file_path))
        return file_path

    async def extract_channel_avatar_url(self, channel_url: str) -> str | None:
        """Extract the channel's avatar/thumbnail URL from YouTube.

        Runs: yt-dlp --dump-single-json --flat-playlist --playlist-items 0 <channel_url>
        Parses the 'thumbnails' list to find the avatar.

        Args:
            channel_url: YouTube channel URL.

        Returns:
            Avatar image URL string, or None if not found.
        """
        logger.info("extracting_channel_avatar", channel_url=channel_url)
        cmd = [
            self._ytdlp,
            "--dump-single-json",
            "--flat-playlist",
            "--playlist-items", "0",
            "--no-warnings",
            "--js-runtimes", "node",
            channel_url,
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=30
            )
        except (asyncio.TimeoutError, FileNotFoundError):
            return None

        if proc.returncode != 0:
            return None

        try:
            data = json.loads(stdout.decode())
        except json.JSONDecodeError:
            return None

        # Look for avatar thumbnail in the channel metadata
        thumbnails = data.get("thumbnails", [])
        # Prefer avatar_uncropped, then any numbered thumbnail (those are avatars)
        for thumb in thumbnails:
            if thumb.get("id") == "avatar_uncropped":
                return thumb.get("url")

        # Fallback: numbered thumbnails (0-5) are avatar at different sizes
        for thumb in thumbnails:
            thumb_id = thumb.get("id", "")
            if thumb_id.isdigit():
                return thumb.get("url")

        return None


# ---------------------------------------------------------------------------
# Singleton access
# ---------------------------------------------------------------------------

_ytdlp_service: YtDlpService | None = None


def init_ytdlp_service(settings: AppSettings) -> YtDlpService:
    """Initialize the global YtDlpService singleton."""
    global _ytdlp_service
    _ytdlp_service = YtDlpService(settings)
    return _ytdlp_service


def get_ytdlp_service() -> YtDlpService:
    """Return the cached YtDlpService. Raises if not initialized."""
    if _ytdlp_service is None:
        raise RuntimeError("YtDlpService not initialized.")
    return _ytdlp_service
