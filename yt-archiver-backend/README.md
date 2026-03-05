# YouTube Archiver Backend

Self-hosted YouTube video archiving platform backend.

## Quick Start

### Prerequisites

- Python 3.11+
- MongoDB running locally
- yt-dlp and ffmpeg binaries in the `lib/` directory

### Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Place yt-dlp and ffmpeg binaries
# macOS example:
# brew install yt-dlp ffmpeg
# cp $(which yt-dlp) lib/yt-dlp
# cp $(which ffmpeg) lib/ffmpeg
```

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
lib/           — External binaries (yt-dlp, ffmpeg)
runtime/       — Runtime data (config, videos, logs)
```
