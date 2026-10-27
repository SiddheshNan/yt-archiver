# yt-archiver

Self-hosted YouTube archiving platform. Save videos to your own server and watch them later from a web UI, even if the original gets taken down.

## Components

| Part | Stack |
|---|---|
| `yt-archiver-backend` | FastAPI, MongoDB, yt-dlp, ffmpeg |
| `yt-archiver-frontend` | React 18, Vite, MUI, Plyr |
| `chrome-extension` | Manifest V3 |

## Features

- Archive a video or a whole channel by URL
- Download queue with progress
- Browse by channel, search across the library
- Web player with a stats overlay
- One-click archiving from a YouTube page via the Chrome extension
- Cookie support so downloads stay at 1080p when YouTube throttles unauthenticated clients

## Running it

Requires Python 3.10, MongoDB, and `yt-dlp` + `ffmpeg` on PATH (or in `lib/`).

```bash
cd yt-archiver-backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
python -m app.main
```

API docs at `http://localhost:8000/docs`.

Frontend:

```bash
cd yt-archiver-frontend
npm install
npm run dev     # port 3100
```

Docker: `python build_prod_docker.py` builds the frontend and bakes it into the backend image.

See `yt-archiver-backend/README.md` for config, binaries and cookie setup.

## Chrome extension

Load `chrome-extension/` unpacked via `chrome://extensions` → Developer mode → Load unpacked, then point it at your instance URL.

## License

MIT
