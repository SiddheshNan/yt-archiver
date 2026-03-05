"""
YouTube URL sanitization utilities.

Normalizes messy YouTube URLs into clean, canonical forms before
handing them off to yt-dlp. Handles:
  - Video URLs with extra playlist/index params
  - Short URLs (youtu.be)
  - Channel URLs in various formats
  - Playlist URLs
"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


# ── Video URL cleaning ────────────────────────────────────────────────

_YT_VIDEO_ID_RE = re.compile(
    r"(?:youtu\.be/|youtube\.com/(?:watch\?.*v=|embed/|v/|shorts/))([a-zA-Z0-9_-]{11})"
)


def clean_video_url(url: str) -> str:
    """Strip playlist/index params from a YouTube video URL.

    Examples:
        https://www.youtube.com/watch?v=abc123&list=PLxyz&index=3
        → https://www.youtube.com/watch?v=abc123

        https://youtu.be/abc123?si=tracking
        → https://www.youtube.com/watch?v=abc123
    """
    url = url.strip()
    match = _YT_VIDEO_ID_RE.search(url)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
    # If we can't parse it, return as-is and let yt-dlp deal with it
    return url


# ── Channel URL cleaning ─────────────────────────────────────────────

_CHANNEL_PATTERNS = [
    # /channel/UC... (canonical ID-based)
    re.compile(r"youtube\.com/(channel/UC[a-zA-Z0-9_-]+)"),
    # /@handle
    re.compile(r"youtube\.com/(@[a-zA-Z0-9_.-]+)"),
    # /c/CustomName (legacy)
    re.compile(r"youtube\.com/(c/[^/?&]+)"),
    # /user/Username (legacy)
    re.compile(r"youtube\.com/(user/[^/?&]+)"),
]


def clean_channel_url(url: str) -> str:
    """Normalize a YouTube channel URL.

    Strips trailing path segments (/videos, /shorts, /playlists, etc.)
    and query params so yt-dlp gets a clean root channel URL.

    Examples:
        https://www.youtube.com/@TaylorSwift/videos?view=0
        → https://www.youtube.com/@TaylorSwift

        https://www.youtube.com/channel/UCxxxxxxx/playlists
        → https://www.youtube.com/channel/UCxxxxxxx
    """
    url = url.strip()
    for pattern in _CHANNEL_PATTERNS:
        match = pattern.search(url)
        if match:
            identifier = match.group(1)
            return f"https://www.youtube.com/{identifier}"
    return url


# ── Playlist URL cleaning ────────────────────────────────────────────


def clean_playlist_url(url: str) -> str:
    """Normalize a YouTube playlist URL.

    Strips video-specific params (v=, index=, etc.) and keeps only the
    list= param so yt-dlp treats it as a full playlist.

    Examples:
        https://www.youtube.com/watch?v=abc123&list=PLxyz&index=5
        → https://www.youtube.com/playlist?list=PLxyz

        https://www.youtube.com/playlist?list=PLxyz&si=tracking
        → https://www.youtube.com/playlist?list=PLxyz
    """
    url = url.strip()
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    list_id = qs.get("list", [None])[0]
    if list_id:
        return f"https://www.youtube.com/playlist?list={list_id}"
    return url


# ── URL type detection ────────────────────────────────────────────────


def detect_url_type(url: str) -> str:
    """Detect the type of YouTube URL.

    Returns:
        "video", "playlist", "channel", or "unknown".
    """
    url = url.strip()
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    path = parsed.path.rstrip("/")

    # Explicit playlist page
    if path == "/playlist" and "list" in qs:
        return "playlist"

    # Video URL (may also contain list= but the primary intent is a video)
    if _YT_VIDEO_ID_RE.search(url):
        return "video"

    # Channel patterns
    for pattern in _CHANNEL_PATTERNS:
        if pattern.search(url):
            return "channel"

    return "unknown"
