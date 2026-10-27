# Runtime folder

Everything YT Archiver writes lives in `runtime/` (`/app/runtime` in Docker, `data/` on the host with Docker Compose). MongoDB holds the metadata separately.

```text
runtime/
├── config/
│   ├── production.yaml      the config, see the reference
│   └── cookies.txt          optional, see Cookies
├── videos/
│   └── <channel name>/
│       ├── <title> [<id>].mp4
│       ├── <title> [<id>].webp           thumbnail (or .jpg)
│       └── <title> [<id>].<lang>.vtt     subtitles
└── logs/
    └── app.log
```

The exact file names come from yt-dlp. MongoDB stores paths relative to `videos/`, so you can move the whole folder (or change `storage.videos_dir`) without breaking the archive.

## Backups

Back up `runtime/` and the MongoDB database together. For MongoDB, `mongodump` works; with Docker Compose:

```bash
docker compose exec mongo mongodump --archive > yt-archiver-db.archive
```
