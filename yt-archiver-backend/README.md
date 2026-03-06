# YouTube Archiver Backend

Self-hosted YouTube video archiving platform backend.

## Quick Start

### Prerequisites

- Python 3.10
- MongoDB
- `yt-dlp` and `ffmpeg` (either in `lib/` subdirectories or available on system `PATH`)

### Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

#### Development Tool Binaries

For local development, the application prioritizes `yt-dlp` and `ffmpeg` binaries placed in platform-specific subdirectories within `lib/`. 

Download the appropriate binaries for your OS and place them in the following structure depending on your platform (win/mac/linux)

```text
lib/
├── ffmpeg/
│   ├── linux/ffmpeg
│   ├── macos/ffmpeg
│   └── windows/ffmpeg.exe
└── ytdlp/
    ├── linux/yt-dlp
    ├── macos/yt-dlp
    └── windows/yt-dlp.exe
```

*Note: If these `lib/` binaries are not found, the application falls back to looking for `yt-dlp` (via pip) and `ffmpeg` (via apt-get, brew, etc.) on your system `PATH`. This fallback is what the production Docker container uses.*

### Run

```bash
# Development (default config: runtime/config/dev.yaml)
python -m app.main

# Production
python -m app.main --config runtime/config/prod.yaml
```

### API Docs

Open http://localhost:8000/docs for Swagger UI.

## Project Structure

```
app/           — Application source code
  config.py    — YAML config loader
  database.py  — MongoDB connection
  models/      — DB document models
  schemas/     — Pydantic API schemas
  repositories/— Data access layer
  services/    — Business logic + external tools
  routers/     — FastAPI API routes
lib/           — Platform-specific external binaries (yt-dlp, ffmpeg)
runtime/       — Runtime data (config, videos, logs)
```
