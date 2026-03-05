"""
Application configuration loaded from YAML files.

All relative paths in the config are resolved against the project root directory.
Config is loaded once at startup and cached as a singleton.
"""

from __future__ import annotations
import shutil

import argparse
import sys
from functools import lru_cache
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
    frontend_build_dir: str = "runtime/frontend-build"

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


class ToolsConfig(BaseModel):
    """External tool binary paths."""

    ytdlp_path: str = "lib/yt-dlp"
    ffmpeg_path: str = "lib/ffmpeg"

    def get_ytdlp_path(self) -> Path:
        """Resolve yt-dlp binary path."""
        path_str = self.ytdlp_path
        if "/" not in path_str and "\\" not in path_str:
            resolved = shutil.which(path_str)
            if resolved:
                return Path(resolved)
        path = Path(path_str)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path.resolve()

    def get_ffmpeg_path(self) -> Path:
        """Resolve ffmpeg binary path."""
        path_str = self.ffmpeg_path
        if "/" not in path_str and "\\" not in path_str:
            resolved = shutil.which(path_str)
            if resolved:
                return Path(resolved)
        path = Path(path_str)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path.resolve()


class DownloadsConfig(BaseModel):
    """Download queue configuration."""

    max_concurrent: int = Field(default=1, ge=1, le=10)
    max_retries: int = Field(default=2, ge=0, le=10)
    timeout: int = Field(default=3600, ge=60,
                         description="Per-video timeout in seconds")


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
