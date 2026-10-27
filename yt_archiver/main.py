"""
FastAPI application entry point.

Handles:
  - Config loading from YAML
  - Structured logging setup
  - MongoDB connection lifecycle
  - Service initialization (YtDlpService, DownloadManager)
  - Router registration
  - CORS configuration
  - Exception handler registration
"""

from __future__ import annotations

import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from yt_archiver import __version__
from yt_archiver.config import (
    AppSettings,
    config_path,
    ensure_config,
    get_settings,
    init_settings,
    parse_args,
)
from yt_archiver.database import init_database, shutdown_database
from yt_archiver.exceptions import register_exception_handlers
from yt_archiver.logging_config import get_logger, setup_logging
from yt_archiver.repositories.channel_repository import ChannelRepository
from yt_archiver.repositories.video_repository import VideoRepository
from yt_archiver.services.download_manager import get_download_manager, init_download_manager
from yt_archiver.services.ytdlp_service import init_ytdlp_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown logic."""
    settings = get_settings()
    logger = get_logger(__name__)

    # ── Startup ─────────────────────────────────────────────────────────
    logger.info("app_starting", port=settings.server.port)

    # Ensure runtime directories exist
    settings.storage.get_videos_path().mkdir(parents=True, exist_ok=True)
    settings.logging.get_log_dir().mkdir(parents=True, exist_ok=True)

    # Database
    db = init_database(settings.database)

    # Services
    ytdlp_svc = init_ytdlp_service(settings)

    video_repo = VideoRepository(db)
    channel_repo = ChannelRepository(db)
    dm = init_download_manager(settings, video_repo, channel_repo, ytdlp_svc)
    await dm.start()

    logger.info("app_started")

    yield

    # ── Shutdown ────────────────────────────────────────────────────────
    logger.info("app_shutting_down")
    await dm.stop()
    shutdown_database()
    logger.info("app_stopped")


def create_app(settings: AppSettings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional pre-loaded settings. If None, expects
                  init_settings() to have been called already.

    Returns:
        Configured FastAPI instance.
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="YouTube Archiver",
        description="Self-hosted YouTube video archiving platform API",
        version=__version__,
        lifespan=lifespan,
    )

    # ── CORS ────────────────────────────────────────────────────────────
    if settings.server.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.server.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # ── Exception handlers ──────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ─────────────────────────────────────────────────────────
    from yt_archiver.routers import channel_router, search_router, video_router

    app.include_router(video_router.router)
    app.include_router(channel_router.router)
    app.include_router(search_router.router)

    # ── Health check ────────────────────────────────────────────────────
    @app.get("/api/health", tags=["Health"])
    def health_check() -> dict:
        return {"status": "ok"}

    # ── Queue status ────────────────────────────────────────────────────
    @app.get("/api/downloads/queue", tags=["Downloads"])
    def queue_status() -> dict:
        dm = get_download_manager()
        return dm.get_status()

    # ── Frontend SPA Serving ────────────────────────────────────────────
    if settings.server.serve_frontend:
        frontend_dir = settings.server.get_frontend_build_dir()

        # Ensure directory exists to avoid startup crashes if user hasn't built yet
        frontend_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = frontend_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        # 1. Mount the assets (/assets, /vite.svg, etc)
        app.mount(
            "/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        # 2. Catch-all route to serve index.html for React Router
        # This explicitly sits at the bottom so it doesn't hijack /api requests
        @app.get("/{full_path:path}", include_in_schema=False)
        def serve_spa(full_path: str):
            # Check if there's an actual file that matches (like favicon.ico)
            file_path = frontend_dir / full_path
            if file_path.is_file():
                return FileResponse(file_path)

            # Fallback to index.html for client-side routing
            index_path = frontend_dir / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return {"error": "Frontend build not found. Please build the React app or disable serve_frontend."}

    return app


# ---------------------------------------------------------------------------
# CLI entry point: python -m yt_archiver -e development
# ---------------------------------------------------------------------------

def make_app() -> FastAPI:
    """Factory behind the "yt_archiver.main:app" import string used by gunicorn and reload.

    The environment comes from YTA_ENV, or from -e when run directly.
    """
    import os

    env = os.environ.get("YTA_ENV")
    if not env:
        # Under gunicorn/uvicorn, sys.argv holds the server's own arguments.
        is_server_cli = any(x in sys.argv[0] for x in ["gunicorn", "uvicorn"])
        env = parse_args([] if is_server_cli else None).env
        # The reload worker re-imports this module in a new process; pass the choice on.
        os.environ["YTA_ENV"] = env

    path = ensure_config(config_path(env))
    settings = init_settings(path)
    setup_logging(settings.logging)
    return create_app(settings)


# Module-level app instance for the "yt_archiver.main:app" import string
app = make_app()


def main() -> None:
    args = parse_args()
    settings = get_settings()

    logger = get_logger(__name__)
    logger.info(
        "starting_server",
        env=args.env,
        host=settings.server.host,
        port=settings.server.port,
    )

    # When reload=True, uvicorn needs an import string, not an object
    if settings.server.reload:
        uvicorn.run(
            "yt_archiver.main:app",
            host=settings.server.host,
            port=settings.server.port,
            reload=True,
            log_level=settings.logging.level.lower(),
        )
    else:
        uvicorn.run(
            app,
            host=settings.server.host,
            port=settings.server.port,
            log_level=settings.logging.level.lower(),
        )


if __name__ == "__main__":
    main()
