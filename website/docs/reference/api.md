# API

The web UI and the extension use a JSON API under `/api`. Interactive docs with every request and response shape are at `/docs` on your instance (Swagger UI).

There is no authentication; see [Security](/docs/security).

In paths, `{id}` is the archive id (`id` in responses), not the YouTube video id.

## Videos

| Method and path | What it does |
|---|---|
| `POST /api/videos` | Archive a video. Body: `{"url": "..."}`. Returns at once with status `pending`. |
| `POST /api/videos/batch` | Archive several videos. Body: `{"urls": ["...", "..."]}`. |
| `POST /api/videos/playlist` | Archive every video in a playlist. Body: `{"url": "..."}`. |
| `GET /api/videos/check?v=<youtube id>` | Whether a YouTube video is archived, and its status. |
| `GET /api/videos` | List videos. Query: `page`, `page_size` (max 100), `status` (`pending`, `downloading`, `completed`, `failed`). |
| `GET /api/videos/{id}` | One video with all its metadata. |
| `POST /api/videos/recommend/home` | Videos for the home page. Body: `{"exclude_ids": [], "limit": 20}`. |
| `GET /api/videos/{id}/related` | Related videos. Query: `limit` (max 50). |
| `POST /api/videos/{id}/rearchive` | Delete the files and download again. |
| `DELETE /api/videos/{id}` | Delete the video and its files. |
| `GET /api/videos/{id}/stream` | The MP4, with range requests for seeking. |
| `GET /api/videos/{id}/thumbnail` | The thumbnail. |
| `GET /api/videos/{id}/subtitles/{lang}` | A subtitle track as VTT. |

## Channels

| Method and path | What it does |
|---|---|
| `POST /api/channels/archive` | Archive every video of a channel. Body: `{"url": "..."}`. |
| `GET /api/channels` | List channels. Query: `page`, `page_size`. |
| `GET /api/channels/{id}` | One channel. |
| `GET /api/channels/{id}/videos` | A channel's videos. Query: `page`, `page_size`. |
| `GET /api/channels/{id}/avatar` | The channel's avatar URL. |

## Other

| Method and path | What it does |
|---|---|
| `GET /api/search?q=<text>` | Full-text search over title, description and channel name. Query: `channel_id`, `page`, `page_size`. |
| `GET /api/downloads/queue` | Queue length and workers. |
| `GET /api/health` | `{"status": "ok"}` when the server is up. |

## Example

```bash
curl -X POST http://localhost:8000/api/videos \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```
