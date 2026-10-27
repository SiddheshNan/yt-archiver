# Changelog

Notable changes to YT Archiver. Versions follow [semantic versioning](https://semver.org).

## Unreleased

- New repository layout: the backend is the `yt_archiver` package at the root, the UI is in `ui/` and the extension in `extension/`.
- Choose the config with `-e development` or `-e production` (or `YTA_ENV`), loading `runtime/config/<env>.yaml`. This replaces `--config` and `APP_CONFIG_PATH`.
- The Docker image builds the UI itself, and `docker compose up -d` runs it together with MongoDB.
- `scripts/build.py` replaces `build_prod_docker.py` and `docker_run.py`.

## v0.1.0

First version.

- Archive a video, a playlist or a whole channel by URL, with a download queue and retries.
- Up to 1080p MP4 with thumbnails and subtitles.
- Browse by channel, search, and a web player with a stats overlay; installable as a PWA.
- Chrome extension to archive from a YouTube page.
- Cookie support to avoid YouTube's bot throttling.
