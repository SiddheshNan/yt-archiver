"""
MongoDB connection management and index creation.

Provides a Database class that manages the PyMongo client lifecycle
and a get_db() dependency for FastAPI route injection.
"""

from __future__ import annotations

from pymongo import MongoClient, TEXT
from pymongo.collection import Collection
from pymongo.database import Database as MongoDatabase

from app.config import DatabaseConfig
from app.logging_config import get_logger

logger = get_logger(__name__)


class Database:
    """Manages the MongoDB client connection and provides collection accessors."""

    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config
        self._client: MongoClient | None = None
        self._db: MongoDatabase | None = None

    def connect(self) -> None:
        """Open the MongoDB connection and verify connectivity."""
        logger.info("connecting_to_mongodb",
                    url=self._config.url, db=self._config.name)
        self._client = MongoClient(self._config.url)
        self._db = self._client[self._config.name]

        # Verify connection
        self._client.admin.command("ping")
        logger.info("mongodb_connected")

    def disconnect(self) -> None:
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            logger.info("mongodb_disconnected")

    @property
    def db(self) -> MongoDatabase:
        """Return the database instance. Raises if not connected."""
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db

    # ── Collection accessors ────────────────────────────────────────────

    @property
    def videos(self) -> Collection:
        return self.db["videos"]

    @property
    def channels(self) -> Collection:
        return self.db["channels"]

    # ── Index management ────────────────────────────────────────────────

    def create_indexes(self) -> None:
        """Create required indexes. Safe to call multiple times (idempotent)."""
        logger.info("creating_indexes")

        # Videos indexes
        self.videos.create_index("video_id", unique=True, name="idx_video_id")
        self.videos.create_index("channel_id", name="idx_channel_id")
        self.videos.create_index("status", name="idx_status")
        self.videos.create_index("created_at", name="idx_created_at")
        self.videos.create_index(
            [("title", TEXT), ("description", TEXT), ("channel_name", TEXT)],
            name="idx_video_text_search",
            weights={"title": 10, "channel_name": 5, "description": 1},
        )

        # Channels indexes
        self.channels.create_index(
            "youtube_channel_id", unique=True, name="idx_youtube_channel_id"
        )
        self.channels.create_index(
            [("name", TEXT)],
            name="idx_channel_text_search",
        )

        logger.info("indexes_created")


# ---------------------------------------------------------------------------
# Singleton + FastAPI dependency
# ---------------------------------------------------------------------------

_database: Database | None = None


def init_database(config: DatabaseConfig) -> Database:
    """Initialize the global Database singleton. Called once at startup."""
    global _database
    _database = Database(config)
    _database.connect()
    _database.create_indexes()
    return _database


def get_database() -> Database:
    """FastAPI dependency — returns the Database singleton."""
    if _database is None:
        raise RuntimeError(
            "Database not initialized. Call init_database() first.")
    return _database


def shutdown_database() -> None:
    """Disconnect the database. Called during app shutdown."""
    if _database is not None:
        _database.disconnect()
