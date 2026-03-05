"""
Structured logging configuration using structlog.

Supports two output formats:
  - "console": colored, human-readable output for development
  - "json": machine-parseable JSON lines for production

Logs are written to both stdout and a rotating log file.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

import structlog

from app.config import LoggingConfig


def setup_logging(config: LoggingConfig) -> None:
    """Configure structlog and stdlib logging from config.

    Args:
        config: LoggingConfig section from the application settings.
    """
    # Ensure log directory exists
    log_dir: Path = config.get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, config.level, logging.INFO)

    # ── stdlib root logger ──────────────────────────────────────────────
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Suppress noisy MongoDB driver logging
    logging.getLogger("pymongo").setLevel(logging.WARNING)

    # Remove existing handlers to avoid duplicates on reload
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Rotating file handler (10 MB per file, keep 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(config.get_log_file_path()),
        maxBytes=10 * 1024 * 1024,
        backupCount=365,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)

    # ── structlog pipeline ──────────────────────────────────────────────
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if config.format == "json":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Apply structlog formatting to all stdlib handlers
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        A bound structlog logger.
    """
    return structlog.get_logger(name)
