# What is YT Archiver?

YT Archiver keeps your own copy of YouTube videos. Paste a video, playlist or channel URL and it downloads every video to your server with [yt-dlp](https://github.com/yt-dlp/yt-dlp). You then browse and watch them from a web UI, even if the original is taken down or made private.

::: warning Early development
YT Archiver is pre-release. Expect rough edges and breaking changes between versions.
:::

## What you get

- Archive a single video, a playlist or a whole channel.
- A download queue with retries and a pause between downloads, so YouTube doesn't rate-limit you.
- MP4 up to 1080p, with the thumbnail and every subtitle track.
- The original title, description, upload date, views, likes and tags.
- Browse by channel, search the library, and play in the browser with subtitles and loop. The UI installs as a PWA.
- A Chrome extension that archives from the YouTube page you're on.

## How it fits together

| Part | What it does |
|---|---|
| **Backend** | A FastAPI server. It runs yt-dlp and ffmpeg, keeps the files in a folder and the metadata in MongoDB, and serves the web UI. |
| **Web UI** | Browse, search, watch and add videos. |
| **Extension** | Adds an Archive button under YouTube videos and talks to your backend. |
| **MongoDB** | Stores videos and channels. Files stay on disk. |

Videos are saved as `<videos folder>/<channel name>/<video>.mp4`, next to their thumbnail and subtitles, so the folder stays useful without YT Archiver.

Next: [install YT Archiver](/docs/installation).
