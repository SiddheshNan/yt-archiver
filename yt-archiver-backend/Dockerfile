FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project metadata and code
COPY pyproject.toml .
COPY app/ app/

# Copy pre-built frontend assets (built by build_prod_docker.py)
COPY frontend-build/ frontend-build/

# Install Python dependencies and the application module
RUN pip install --no-cache-dir .

# Create runtime directories
# These will be typically mounted via docker-compose/volumes,
# but we create them here to ensure the container runs standalone too
RUN mkdir -p runtime/videos runtime/logs runtime/config

EXPOSE 8000

# Run the FastAPI server using Gunicorn (ASGI process manager)
# Config is auto-generated from env vars if not found at the given path
ENV APP_CONFIG_PATH="runtime/config/prod.yaml"
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
