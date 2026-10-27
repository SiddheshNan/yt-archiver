---
layout: home

hero:
  name: YT Archiver
  text: Your own YouTube archive.
  tagline: Save videos and whole channels to your server and watch them from a web UI, even after the original is gone.
  image:
    src: /logo.svg
    alt: YT Archiver
  actions:
    - theme: brand
      text: Get started
      link: /docs/
    - theme: alt
      text: Installation
      link: /docs/installation
    - theme: alt
      text: GitHub
      link: https://github.com/SiddheshNan/yt-archiver

features:
  - title: Videos, playlists, channels
    details: Paste a URL. Every video is queued and downloaded one after another, with retries.
  - title: 1080p with subtitles
    details: MP4 up to 1080p, the thumbnail and every subtitle track, in a folder per channel.
  - title: Watch anywhere
    details: Browse by channel, search, and play in the browser. Installs as a PWA.
  - title: Archive from YouTube
    details: The Chrome extension adds an Archive button and shows what you already have.
  - title: Yours
    details: Plain MP4 files on your disk and metadata in your own MongoDB. No account, no cloud.
  - title: One command
    details: docker compose up -d runs it with MongoDB.
---

<div class="home-section">

## Install

<p class="lead">You need Docker with Compose. Then open http://localhost:8000.</p>

```bash
git clone https://github.com/SiddheshNan/yt-archiver.git
cd yt-archiver
docker compose up -d
```

</div>
