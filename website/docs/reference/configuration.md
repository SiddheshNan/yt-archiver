# Configuration file

YT Archiver reads `runtime/config/<env>.yaml`, where `<env>` comes from `-e` or the `YTA_ENV` variable:

```bash
python -m yt_archiver -e production     # runtime/config/production.yaml
```

The Docker image sets `YTA_ENV=production`. With Docker Compose the file is `data/config/production.yaml` on the host.

Relative paths are resolved against the installation folder (`/app` in Docker). Restart YT Archiver after editing.

## Example

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  reload: false
  cors_origins:
    - "*"
  serve_frontend: true
  frontend_build_dir: "ui/dist"

database:
  url: "mongodb://localhost:27017"
  name: "yt_archiver_prod"

storage:
  videos_dir: "runtime/videos"

downloads:
  max_concurrent: 1
  max_retries: 3
  timeout: 7200
  cooldown_seconds: 10
  retries: 3
  cookies_file: "runtime/config/cookies.txt"
  browser_cookies: null

logging:
  level: "INFO"
  format: "json"
  log_dir: "runtime/logs"
  log_file: "app.log"
```

## server

| Key | Default | Meaning |
|---|---|---|
| `host` | `0.0.0.0` | Address to listen on. |
| `port` | `8000` | Port to listen on. |
| `reload` | `false` | Restart on code changes. For development only. |
| `cors_origins` | `[]` | Origins allowed to call the API from a browser. The [extension](/docs/extension) needs `https://www.youtube.com`, or `"*"`. |
| `serve_frontend` | `false` | Serve the built web UI from the same port. |
| `frontend_build_dir` | `ui/dist` | Where the built UI is. |

## database

| Key | Default | Meaning |
|---|---|---|
| `url` | `mongodb://localhost:27017` | MongoDB connection string. |
| `name` | `yt_archiver` | Database name. |

## storage

| Key | Default | Meaning |
|---|---|---|
| `videos_dir` | `runtime/videos` | Where videos, thumbnails and subtitles are saved, in a folder per channel. |

## downloads

| Key | Default | Meaning |
|---|---|---|
| `max_concurrent` | `1` | Downloads that run at the same time (1–10). |
| `max_retries` | `2` | Times a failed download is queued again before the video is marked failed. |
| `timeout` | `3600` | Seconds one download may take. |
| `cooldown_seconds` | `10` | Pause after each download, to avoid YouTube rate limits. |
| `retries` | `3` | yt-dlp's own retries for network errors within one download. |
| `cookies_file` | none | Netscape `cookies.txt` passed to yt-dlp. See [cookies](/docs/cookies). |
| `browser_cookies` | none | Browser to read cookies from (`chrome`, `firefox`, `safari`, `edge`, …) when `cookies_file` isn't set or doesn't exist. |

## logging

| Key | Default | Meaning |
|---|---|---|
| `level` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`. |
| `format` | `console` | `console` for readable lines, `json` for one JSON object per line. |
| `log_dir` | `runtime/logs` | Folder for the log file. |
| `log_file` | `app.log` | Log file name. |

## Environment variables

When the config file doesn't exist, YT Archiver writes one from these variables on start. After that the file wins and the variables are ignored.

| Variable | Default | Sets |
|---|---|---|
| `YTA_SERVER_PORT` | `8000` | `server.port` |
| `YTA_CORS_ORIGINS` | localhost, YouTube and `*` | `server.cors_origins`, comma-separated |
| `YTA_SERVE_FRONTEND` | `true` | `server.serve_frontend` |
| `YTA_DB_URL` | `mongodb://host.docker.internal:27017` | `database.url` |
| `YTA_DB_NAME` | `yt_archiver` | `database.name` |
| `YTA_VIDEOS_DIR` | `runtime/videos` | `storage.videos_dir` |
| `YTA_MAX_CONCURRENT` | `1` | `downloads.max_concurrent` |
| `YTA_MAX_RETRIES` | `3` | `downloads.max_retries` |
| `YTA_TIMEOUT` | `7200` | `downloads.timeout` |
| `YTA_COOLDOWN_SECONDS` | `10` | `downloads.cooldown_seconds` |
| `YTA_RETRIES` | `3` | `downloads.retries` |
| `YTA_COOKIES_FILE` | none | `downloads.cookies_file` |
| `YTA_BROWSER_COOKIES` | none | `downloads.browser_cookies` |
| `YTA_LOG_LEVEL` | `INFO` | `logging.level` |
| `YTA_LOG_FORMAT` | `json` | `logging.format` |

`YTA_ENV` (`development` or `production`) picks the config file and is always read.
