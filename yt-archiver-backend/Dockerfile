FROM python:3.10-slim

# Install system dependencies (ffmpeg is required for yt-dlp)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project metadata and code
COPY pyproject.toml .
COPY app/ app/
COPY lib/ lib/

# Install Python dependencies and the application module
RUN pip install --no-cache-dir .
# Note: In a production environment, you should copy the built frontend 
# into runtime/frontend-build before building this container, 
# or via a multi-stage Dockerfile that builds the React project.

# Create runtime directories
# These will be typically mounted via docker-compose/volumes,
# but we create them here to ensure the container runs standalone too
RUN mkdir -p runtime/videos runtime/logs runtime/frontend-build/assets runtime/config

EXPOSE 8000

# Run the FastAPI server using Gunicorn (ASGI process manager)
# It expects a config file mounted at runtime/config/prod.yaml
# We also pass the config path as an environment variable so app.main can pick it up
ENV APP_CONFIG_PATH="runtime/config/prod.yaml"
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
