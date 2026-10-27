FROM node:22-slim AS ui
WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ ./
RUN npm run build

FROM python:3.10-slim

# yt-dlp needs ffmpeg to merge streams and Node to solve YouTube's JS challenges
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY yt_archiver/ yt_archiver/
RUN pip install --no-cache-dir .
COPY --from=ui /ui/dist ui/dist

# runtime/ is meant to be a volume. With no config in it, one is generated from YTA_* variables on first start.
RUN mkdir -p runtime/videos runtime/logs runtime/config
ENV YTA_ENV=production
EXPOSE 8000
CMD ["gunicorn", "yt_archiver.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
