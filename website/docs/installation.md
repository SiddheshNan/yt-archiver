# Installation

YT Archiver runs anywhere Docker runs. You can also run it straight from source.

## Docker Compose

This runs YT Archiver and MongoDB together.

```bash
git clone https://github.com/SiddheshNan/yt-archiver.git
cd yt-archiver
docker compose up -d
```

Open http://localhost:8000.

- Videos, logs and the config are in `data/` next to `docker-compose.yml`.
- MongoDB keeps its data in the `mongo-data` Docker volume.

On first start the config is written to `data/config/production.yaml`. Edit it and run `docker compose restart yt-archiver` to apply changes; see the [configuration reference](/docs/reference/configuration).

YT Archiver has no login. Before you make it reachable from outside your network, read [Security](/docs/security).

## Docker without Compose

If you already have MongoDB, build the image and run it on its own:

```bash
docker build -t yt-archiver .
docker run -d --name yt-archiver --restart unless-stopped \
  -p 8000:8000 \
  -v "$PWD/data:/app/runtime" \
  -e YTA_DB_URL=mongodb://host.docker.internal:27017 \
  yt-archiver
```

`YTA_DB_URL` defaults to `mongodb://host.docker.internal:27017`, which reaches MongoDB on the Docker host on macOS and Windows. On Linux add `--add-host=host.docker.internal:host-gateway`, or use your MongoDB's address.

The `YTA_*` variables are only read when there is no config file yet. They are listed in the [configuration reference](/docs/reference/configuration#environment-variables).

## Without Docker

You need:

- Python 3.10 or newer
- MongoDB
- `ffmpeg`
- Node.js, which yt-dlp uses to solve YouTube's JavaScript challenges
- `yt-dlp`, installed with YT Archiver by pip, or a standalone binary (see below)

```bash
git clone https://github.com/SiddheshNan/yt-archiver.git
cd yt-archiver
python -m venv .venv && source .venv/bin/activate
pip install .
cd ui && npm ci && npm run build && cd ..
python -m yt_archiver -e production
```

`-e production` loads `runtime/config/production.yaml`, which serves the built UI and connects to MongoDB on `localhost:27017`. Open http://localhost:8000.

### Local yt-dlp and ffmpeg binaries

YT Archiver first looks for binaries in `lib/`, then on PATH. Drop standalone builds here to pin a version or to avoid a system install:

```text
lib/
├── ffmpeg/
│   ├── linux/ffmpeg
│   ├── macos/ffmpeg
│   └── windows/ffmpeg.exe
└── ytdlp/
    ├── linux/yt-dlp
    ├── macos/yt-dlp
    └── windows/yt-dlp.exe
```

## Next

- [Archive your first video](/docs/archiving)
- [Set up cookies](/docs/cookies) if downloads come out at 360p
- [Install the Chrome extension](/docs/extension)
