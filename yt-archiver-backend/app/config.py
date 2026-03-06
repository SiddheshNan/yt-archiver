"""
Application configuration loaded from YAML files.

All relative paths in the config are resolved against the project root directory.
Config is loaded once at startup and cached as a singleton.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

# Project root: the directory containing the `app` package
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class ServerConfig(BaseModel):
    """HTTP server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    cors_origins: list[str] = Field(default_factory=list)
    serve_frontend: bool = False
    frontend_build_dir: str = "frontend-build"

    def get_frontend_build_dir(self) -> Path:
        """Resolve frontend build directory relative to project root."""
        path = Path(self.frontend_build_dir)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path.resolve()


class DatabaseConfig(BaseModel):
    """MongoDB connection configuration."""

    url: str = "mongodb://localhost:27017"
    name: str = "yt_archiver"


class StorageConfig(BaseModel):
    """Video file storage configuration."""

    videos_dir: str = "runtime/videos"

    def get_videos_path(self) -> Path:
        """Resolve videos_dir relative to project root."""
        path = Path(self.videos_dir)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path.resolve()


def _platform_suffix() -> str:
    """Return the platform suffix for tool binaries."""
    if sys.platform.startswith("linux"):
        return "linux"
    elif sys.platform == "darwin":
        return "macos"
    elif sys.platform == "win32":
        return "windows"
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")


class ToolsConfig(BaseModel):
    """External tool binary resolution.

    Binaries are stored per-platform under lib/ffmpeg/ and lib/ytdlp/.
    Layout:
        lib/ffmpeg/{linux,macos,windows}/ffmpeg[.exe]
        lib/ytdlp/{linux,macos,windows}/yt-dlp[.exe]

    The correct subdirectory is selected automatically based on the OS.
    """

    def get_ytdlp_path(self) -> Path:
        """Resolve the platform-specific yt-dlp binary from lib/ytdlp/."""
        suffix = _platform_suffix()
        name = "yt-dlp.exe" if suffix == "windows" else "yt-dlp"
        path = PROJECT_ROOT / "lib" / "ytdlp" / suffix / name
        return path.resolve()

    def get_ffmpeg_path(self) -> Path:
        """Resolve the platform-specific ffmpeg binary from lib/ffmpeg/."""
        suffix = _platform_suffix()
        name = "ffmpeg.exe" if suffix == "windows" else "ffmpeg"
        path = PROJECT_ROOT / "lib" / "ffmpeg" / suffix / name
        return path.resolve()


class DownloadsConfig(BaseModel):
    """Download queue configuration."""

    max_concurrent: int = Field(default=1, ge=1, le=10)
    max_retries: int = Field(default=2, ge=0, le=10)
    timeout: int = Field(default=3600, ge=60,
                         description="Per-video timeout in seconds")
    cooldown_seconds: int = Field(default=10, ge=0,
                                  description="Delay between consecutive downloads")
    retries: int = Field(default=3, ge=0, le=10,
                         description="yt-dlp retries per download")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    format: Literal["json", "console"] = "console"
    log_dir: str = "runtime/logs"
    log_file: str = "app.log"

    def get_log_dir(self) -> Path:
        """Resolve log directory relative to project root."""
        path = Path(self.log_dir)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path.resolve()

    def get_log_file_path(self) -> Path:
        """Full path to the log file."""
        return self.get_log_dir() / self.log_file


class AppSettings(BaseModel):
    """Root application settings — aggregates all config sections."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    downloads: DownloadsConfig = Field(default_factory=DownloadsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


# ---------------------------------------------------------------------------
# Default config generation from environment variables
# ---------------------------------------------------------------------------

_DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:3100",
    "https://www.youtube.com",
    "https://m.youtube.com",
    "https://music.youtube.com",
]


def generate_default_config() -> dict:
    """Build a config dict from YTA_* environment variables with defaults.

    This is used when no config file exists (e.g. first run in Docker).
    Every value has a sensible default so the app can start without
    any env vars set at all.
    """
    cors_raw = os.environ.get("YTA_CORS_ORIGINS", "")
    cors_origins = (
        [o.strip() for o in cors_raw.split(",") if o.strip()]
        if cors_raw
        else _DEFAULT_CORS_ORIGINS
    )

    return {
        "server": {
            "host": "0.0.0.0",
            "port": int(os.environ.get("YTA_SERVER_PORT", "8000")),
            "reload": False,
            "cors_origins": cors_origins,
            "serve_frontend": os.environ.get(
                "YTA_SERVE_FRONTEND", "true"
            ).lower() in ("true", "1", "yes"),
            "frontend_build_dir": "frontend-build",
        },
        "database": {
            "url": os.environ.get("YTA_DB_URL", "mongodb://localhost:27017"),
            "name": os.environ.get("YTA_DB_NAME", "yt_archiver"),
        },
        "storage": {
            "videos_dir": os.environ.get("YTA_VIDEOS_DIR", "runtime/videos"),
        },
        "downloads": {
            "max_concurrent": int(
                os.environ.get("YTA_MAX_CONCURRENT", "1")
            ),
            "max_retries": 3,
            "timeout": 7200,
            "cooldown_seconds": 10,
            "retries": 3,
        },
        "logging": {
            "level": os.environ.get("YTA_LOG_LEVEL", "INFO"),
            "format": os.environ.get("YTA_LOG_FORMAT", "json"),
            "log_dir": "runtime/logs",
            "log_file": "app.log",
        },
    }


def ensure_config(config_path: str | Path) -> Path:
    """Ensure the config file exists; create from env vars if missing.

    If the file already exists it is left untouched.

    Returns:
        Resolved absolute path to the config file.
    """
    path = Path(config_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        config = generate_default_config()
        with open(path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return path


def load_config(config_path: str | Path) -> AppSettings:
    """Load and validate configuration from a YAML file.

    Args:
        config_path: Path to the YAML config file. If relative, resolved
                     against the project root.

    Returns:
        Validated AppSettings instance.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the YAML is malformed.
        pydantic.ValidationError: If the config values are invalid.
    """
    path = Path(config_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f) or {}

    return AppSettings(**raw)


# ---------------------------------------------------------------------------
# Singleton access
# ---------------------------------------------------------------------------

_settings: AppSettings | None = None


def init_settings(config_path: str | Path) -> AppSettings:
    """Initialize the global settings singleton. Called once at startup."""
    global _settings
    _settings = load_config(config_path)
    return _settings


def get_settings() -> AppSettings:
    """Return the cached settings. Raises if not yet initialized."""
    if _settings is None:
        raise RuntimeError(
            "Settings not initialized. Call init_settings() during app startup."
        )
    return _settings


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the application."""
    parser = argparse.ArgumentParser(description="YouTube Archiver Backend")
    parser.add_argument(
        "--config",
        type=str,
        default="runtime/config/dev.yaml",
        help="Path to YAML config file (default: runtime/config/dev.yaml)",
    )
    return parser.parse_args(argv if argv is not None else sys.argv[1:])
