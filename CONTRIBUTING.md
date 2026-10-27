# Contributing to YT Archiver

Thanks for helping. YT Archiver is early, so for anything bigger than a bug fix please open an issue first and describe what you want to change. It saves both of us a rewrite.

## Setup

You need Python 3.10+, Node 20+ and MongoDB. yt-dlp also needs `ffmpeg` and Node; put `yt-dlp` and `ffmpeg` on PATH, or drop the binaries into `lib/` (see [installation](website/docs/installation.md#without-docker)). Docker is only needed to build the image.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m yt_archiver -e development
cd ui && npm install && npm run dev
```

Open http://localhost:3100. The UI talks to the API on http://localhost:8000, which reloads on code changes (`reload: true` in `runtime/config/development.yaml`). Everything created at runtime (videos, logs, cookies) lands in `runtime/` and is gitignored.

## Layout

```
yt_archiver/        FastAPI backend
  main.py           app factory, startup and the CLI
  config.py         loads runtime/config/<env>.yaml
  routers/          HTTP handlers under /api
  services/         yt-dlp wrapper, download queue, video and channel logic
  repositories/     MongoDB queries
  models/ schemas/  database documents and API shapes
ui/                 React + MUI web UI
extension/          Chrome extension (Manifest V3)
runtime/config/     development.yaml and production.yaml
lib/                optional local yt-dlp and ffmpeg binaries, per OS
scripts/build.py    release build
docs/               design doc
website/            website and user docs (VitePress)
```

[docs/DESIGN.md](docs/DESIGN.md) explains how the pieces work. Read the relevant section before changing how something behaves, and update it in the same pull request when you do.

## Before you open a pull request

```bash
ruff check .
cd ui && npm run build
```

- Keep changes focused; one pull request per fix or feature.
- Match the code around you. Comments explain why, not what, and only where it isn't obvious.
- New config keys go into both files in `runtime/config/` and into `generate_default_config` in `yt_archiver/config.py`, and are documented in `website/docs/reference/configuration.md`.
- When the API's JSON changes, update the UI and, if it uses that endpoint, the extension in the same change.

## Releases

`./scripts/build.py` asks for the version, writes it everywhere, builds the Docker image and zips the extension into `dist/`. Pushing a `vX.Y.Z` tag publishes the image to GitHub Container Registry and the extension zip to a GitHub release.

By contributing you agree that your work is licensed under the [MIT license](LICENSE).
