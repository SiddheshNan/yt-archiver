# Archiving

Click **+** in the top bar of the web UI and paste a URL. Or use the [Chrome extension](/docs/extension) from the YouTube page.

## Videos

A video URL (`youtube.com/watch?v=…`, `youtu.be/…`, Shorts) is added right away with the status **pending**. YT Archiver fetches its metadata, then queues the download. Tracking parameters such as `&t=` or `&list=` are removed first.

A video that is already in the archive is rejected, so adding the same URL twice is harmless.

## Playlists and channels

Paste a playlist URL or a channel URL. YT Archiver lists every video and queues the ones you don't have yet. Their metadata is fetched one at a time, right before each download, so a big channel doesn't flood YouTube with requests. Expect a large channel to take hours.

Archiving a channel again later picks up only its new videos.

## The queue

The queue on the Add page lists pending, downloading and failed videos; you can remove them from there. Downloads run one at a time by default (`downloads.max_concurrent`), with a pause between them (`downloads.cooldown_seconds`). A failed download is retried (`downloads.max_retries`) before the video is marked **failed** with the error.

The queue is kept in memory. If the server restarts, videos that were still waiting stay **pending**; re-archive them from their page.

## Re-archiving and deleting

**Rearchive** on a video's page checks that the video is still on YouTube, removes its files and downloads it again. Use it for a failed or low-quality download. **Delete** removes the video and its files.

## What gets saved

For each video:

- MP4, best quality up to 1080p
- the thumbnail
- every subtitle track YouTube offers, as VTT
- title, description, upload date, duration, views, likes, tags and categories, plus the dislike count from [Return YouTube Dislike](https://returnyoutubedislike.com)

Files go to `<videos_dir>/<channel name>/`.
