# Upgrading

## Docker Compose

```bash
git pull
docker compose up -d --build
```

Your videos, config and database live in `data/` and the `mongo-data` volume, so they survive the rebuild. Read the [changelog](/changelog) first for anything that needs a manual step.

## From source

```bash
git pull
pip install .
cd ui && npm ci && npm run build && cd ..
```

Then restart `python -m yt_archiver -e production`.

## Updating yt-dlp

YouTube changes often, and most download failures are fixed by a newer yt-dlp. Rebuilding the Docker image installs the latest one. From source, run `pip install -U yt-dlp`, or replace the binary in `lib/` if you use one.
