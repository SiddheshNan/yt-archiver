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
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import AppSettings, init_settings, get_settings, parse_args, ensure_config
from app.database import init_database, shutdown_database, get_database
from app.exceptions import register_exception_handlers
from app.logging_config import get_logger, setup_logging
from app.repositories.channel_repository import ChannelRepository
from app.repositories.video_repository import VideoRepository
from app.services.download_manager import init_download_manager, get_download_manager
from app.services.ytdlp_service import init_ytdlp_service


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
        version="0.1.0",
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
    from app.routers import video_router, channel_router, search_router

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
# CLI entry point: python -m app.main --config runtime/config/dev.yaml
# ---------------------------------------------------------------------------

def make_app() -> FastAPI:
    """Factory used by uvicorn/gunicorn reload (import string: 'app.main:app').

    Initializes settings + logging if not already done, then creates the app.
    """
    import os
    config_path = os.environ.get("APP_CONFIG_PATH")

    if config_path:
        # Ensure config exists (auto-create from env vars if missing)
        ensure_config(config_path)
        settings = init_settings(config_path)
    else:
        # Fallback to argparse for local python -m execution
        # Pass empty list if we detect gunicorn/uvicorn to avoid argparse parsing
        # the WSGI/ASGI server arguments and crashing.
        import sys
        is_server_cli = any(x in sys.argv[0] for x in ["gunicorn", "uvicorn"])
        args = parse_args([] if is_server_cli else None)
        ensure_config(args.config)
        settings = init_settings(args.config)

    setup_logging(settings.logging)
    return create_app(settings)


# Module-level app instance for uvicorn import string ("app.main:app")
app = make_app()


def main() -> None:
    args = parse_args()
    settings = get_settings()

    logger = get_logger(__name__)
    logger.info(
        "starting_server",
        config=args.config,
        host=settings.server.host,
        port=settings.server.port,
    )

    # When reload=True, uvicorn needs an import string, not an object
    if settings.server.reload:
        uvicorn.run(
            "app.main:app",
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
