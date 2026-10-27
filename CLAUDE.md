# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

YT Archiver: a self-hosted YouTube archive. A FastAPI backend downloads videos with yt-dlp into a folder and keeps metadata in MongoDB; a React UI browses and plays them; a Chrome extension archives from youtube.com. [docs/DESIGN.md](docs/DESIGN.md) describes the download flow, config and known limitations; read the relevant section before changing behavior.

## Commands

Backend (Python 3.10+, package `yt_archiver` at the repo root):

```bash
pip install -e ".[dev]"
python -m yt_archiver -e development       # API on :8000, Swagger at /docs, reloads on change
ruff check .
```

There are no tests yet. Running needs MongoDB, plus `yt-dlp`, `ffmpeg` and Node (yt-dlp is called with `--js-runtimes node`).

UI (`ui/`, React 18 + Vite + MUI, plain JSX, no test runner or linter):

```bash
cd ui && npm install && npm run dev        # :3100, calls http://localhost:8000
npm run build
```

Docs site: `cd website && npm install && npm run dev` (VitePress).

Release: `scripts/build.py` writes the version into `yt_archiver/__init__.py`, `pyproject.toml`, `ui/package.json` and `extension/manifest.json`, builds the Docker image (which builds the UI itself) and zips the extension into `dist/`. A `vX.Y.Z` tag runs `.github/workflows/release.yml`, which pushes the image to GHCR.

## Config

`-e development|production` or `YTA_ENV` selects `runtime/config/<env>.yaml`. Relative paths resolve against the repo root (`PROJECT_ROOT` in `config.py`). A missing file is generated from `YTA_*` env vars (`generate_default_config`), which is how Docker starts with an empty `runtime/` volume. New keys go into both YAML files, the Pydantic models and `generate_default_config`, and into `website/docs/reference/configuration.md`.

## Architecture

- `main.py`: `make_app()` loads config and logging at import (the `yt_archiver.main:app` import string is used by gunicorn and uvicorn reload); `lifespan` connects MongoDB and starts the download manager; in production it also serves `ui/dist` with an SPA fallback.
- `routers/` → `services/` → `repositories/`. Routers build services per request from module-level singletons (`get_settings`, `get_download_manager`, `get_ytdlp_service`). `models/` are MongoDB document shapes and serializers; `schemas/` are Pydantic API shapes. Errors are raised as the classes in `exceptions.py` and mapped to responses there.
- `services/ytdlp_service.py`: every yt-dlp invocation (metadata, flat playlist, download, avatar) and cookie arguments.
- `services/download_manager.py`: in-memory asyncio queue with `downloads.max_concurrent` workers, cooldown between jobs, retries, and post-download bookkeeping (thumbnail, subtitles, relative paths).
- `services/video_service.py`: add / batch / channel / playlist archiving, re-archive, delete, listing, search and file lookup.
- Logging is structlog (`logging_config.py`): log event names in snake_case with key-value context, e.g. `logger.info("job_enqueued", video_id=...)`.

UI (`ui/src/`): `pages/` per route, `components/`, API calls in `services/api.js` over the axios instance, MUI theme in `theme/`. The extension (`extension/content.js`) calls `/api/videos/check` and the add endpoints directly, so keep those stable or update it too.

## Conventions

- File paths in MongoDB are stored relative to `storage.videos_dir`.
- Keep yt-dlp calls in `ytdlp_service.py`; don't shell out elsewhere.
