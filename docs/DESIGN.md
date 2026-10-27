# Design

How YT Archiver works inside. User-facing docs live in [website/docs](../website/docs).

## Pieces

- **Backend** (`yt_archiver/`): a FastAPI app. It stores metadata in MongoDB, runs `yt-dlp` and `ffmpeg` as subprocesses, keeps files under `storage.videos_dir`, and in production serves the built UI too.
- **UI** (`ui/`): React 18, MUI and Plyr, built with Vite. In development it calls `http://localhost:8000`; in production it is served from the backend and calls the same origin.
- **Extension** (`extension/`): a Manifest V3 content script on youtube.com. It asks the backend whether the open video is archived and adds an Archive button. Its popup stores the instance URL and optional Cloudflare Access service-token headers.

## Config

`python -m yt_archiver -e <env>` (or `YTA_ENV=<env>`) loads `runtime/config/<env>.yaml`, where `<env>` is `development` or `production`. All relative paths in the config resolve against the repository root, which is `/app` in the Docker image.

If the file doesn't exist, `ensure_config` writes one from `YTA_*` environment variables (`generate_default_config` in `config.py`). This is how the Docker image starts with an empty `runtime/` volume: the first start writes `runtime/config/production.yaml`, and later starts read it and ignore the variables.

## Layers

`routers/` → `services/` → `repositories/` → MongoDB. Routers build their service per request from the module-level singletons (`get_settings`, `get_download_manager`, `get_ytdlp_service`). `models/` define the stored documents and how they serialize; `schemas/` are the Pydantic request and response shapes.

Collections:

- `videos`: one document per YouTube video id, holding YouTube metadata (title, counts, tags), the file, thumbnail and subtitle paths relative to `videos_dir`, and `status`: `pending` → `downloading` → `completed` or `failed` with `error_message`.
- `channels`: created on demand from video metadata, keyed by YouTube channel id.

## Archiving a video

1. `POST /api/videos` cleans the URL, reads the video id locally and rejects duplicates. It creates a `pending` placeholder and returns at once.
2. A background task fetches metadata (`yt-dlp --dump-json`), fills in the document, finds or creates the channel and enqueues a `DownloadJob`.
3. `DownloadManager` runs `downloads.max_concurrent` asyncio workers over an in-memory queue. A worker skips jobs whose video was deleted while queued, marks the video `downloading` and runs yt-dlp: best video up to 1080p plus best audio, merged to MP4, with the thumbnail and all subtitle tracks (VTT, live chat excluded). Files go to `<videos_dir>/<channel name>/`.
4. On success it stores the file path, size, thumbnail and subtitle tracks and marks the video `completed`. On failure it retries up to `downloads.max_retries` times, then marks it `failed`.
5. Each worker waits `downloads.cooldown_seconds` between jobs to avoid YouTube rate limits.

Channels and playlists (`POST /api/channels/archive`, `POST /api/videos/playlist`) list the entries flat, create a skeleton document per new video and enqueue jobs with `needs_metadata`. The worker then fetches metadata right before each download, so a large channel doesn't send a burst of metadata requests.

Dislike counts come from the Return YouTube Dislike API and are optional.

## Playback

`GET /api/videos/{id}/stream` serves the MP4 with range requests, so the player can seek. Thumbnails and subtitles have their own endpoints. The UI is a PWA with a network-first service worker.

## Cookies

YouTube serves throttled formats (often 360p) to clients it thinks are bots. yt-dlp gets `--cookies <file>` when `downloads.cookies_file` exists, otherwise `--cookies-from-browser <name>` when `downloads.browser_cookies` is set. Every yt-dlp call also gets `--js-runtimes node`, so Node must be installed.

## Tools

`tools` resolves `yt-dlp` and `ffmpeg`: first `lib/<tool>/<linux|macos|windows>/`, then PATH. The Docker image installs ffmpeg and Node from apt and yt-dlp from pip.

## Known limitations

- The download queue lives in memory. Jobs queued when the server stops are lost and their videos stay `pending` until re-archived.
- The Docker image runs gunicorn with 4 workers, and each worker has its own queue, so up to 4 downloads can run at once and `/api/downloads/queue` shows one worker's view.
- No authentication.
