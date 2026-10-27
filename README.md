<p align="center"><img src="assets/logo.svg" width="96" alt="YT Archiver logo"></p>

<h1 align="center">YT Archiver</h1>

<p align="center">Your own YouTube archive.<br>Save videos and whole channels to your server and watch them from a web UI, even after the original is gone.</p>

<p align="center">
  <a href="website/docs/index.md">Docs</a> ·
  <a href="website/docs/installation.md">Installation</a> ·
  <a href="website/docs/reference/configuration.md">Configuration</a> ·
  <a href="CHANGELOG.md">Changelog</a>
</p>

> **Status: early.** YT Archiver works, but expect rough edges and breaking changes before 1.0.

## Features

- Archive a single video, a playlist or a whole channel by URL
- A download queue with retries, shown live in the UI
- Up to 1080p MP4 with thumbnails and every subtitle track
- Browse by channel and search across the library
- A web player with loop, subtitles and a stats overlay; installs as a PWA
- One-click archiving from YouTube with the Chrome extension
- Cookie support, so downloads stay at 1080p when YouTube throttles unauthenticated clients

## Quick start

You need Docker with Compose.

```bash
git clone https://github.com/SiddheshNan/yt-archiver.git
cd yt-archiver
docker compose up -d
```

Open http://localhost:8000. Videos, logs and the config land in `data/`; MongoDB keeps its data in a Docker volume.

YT Archiver has no login of its own. Keep it on your own network, or put it behind a VPN or an access proxy such as Cloudflare Access ([security](website/docs/security.md)).

See the [installation guide](website/docs/installation.md) for plain `docker run`, running without Docker, and [cookies](website/docs/cookies.md) to keep downloads at 1080p.

## Chrome extension

The extension adds an Archive button under YouTube videos and shows when a video is already in your archive. Load `extension/` unpacked from `chrome://extensions` (Developer mode → Load unpacked), then set your instance URL in its popup. See [the extension docs](website/docs/extension.md).

## Documentation

- [Docs](website/docs/index.md): install, archive, watch, cookies and the extension. Source in [website/](website).
- [DESIGN.md](docs/DESIGN.md): how YT Archiver works inside.

Run the docs site locally:

```bash
cd website && npm install && npm run dev
```

## Development

You need Python 3.10+, Node 20+, MongoDB, and `yt-dlp` and `ffmpeg` on PATH or in `lib/`.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m yt_archiver -e development
cd ui && npm install && npm run dev
```

The API runs on http://localhost:8000 (Swagger at `/docs`) and the UI on http://localhost:3100. See [CONTRIBUTING.md](CONTRIBUTING.md) for the project layout and conventions.

## Contributing

Issues and pull requests are welcome. Please open an issue to discuss bigger changes first. See [CONTRIBUTING.md](CONTRIBUTING.md), and report security issues as described in [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE). Archive only what you have the right to keep; you are responsible for complying with YouTube's terms and copyright law where you live.
