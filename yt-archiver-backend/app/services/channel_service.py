"""
Channel service — business logic for channel operations.
"""

from __future__ import annotations

from app.exceptions import NotFoundError
from app.logging_config import get_logger
from app.models.channel import serialize_channel
from app.repositories.channel_repository import ChannelRepository
from app.schemas.common import PaginatedResponse
from app.schemas.channel import ChannelResponse

logger = get_logger(__name__)


class ChannelService:
    """Business logic layer for channel management."""

    def __init__(self, channel_repo: ChannelRepository) -> None:
        self._channel_repo = channel_repo

    def list_channels(
        self,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse[ChannelResponse]:
        """Return a paginated list of all channels.

        Args:
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            PaginatedResponse containing ChannelResponse items.
        """
        skip = (page - 1) * page_size
        docs, total = self._channel_repo.list_all(skip=skip, limit=page_size)
        items = [ChannelResponse(**serialize_channel(doc)) for doc in docs]
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_channel(self, channel_id: str) -> ChannelResponse:
        """Get a single channel by its MongoDB ID.

        Args:
            channel_id: MongoDB ObjectId string.

        Returns:
            ChannelResponse.

        Raises:
            NotFoundError: If channel does not exist.
        """
        doc = self._channel_repo.find_by_id(channel_id)
        if doc is None:
            raise NotFoundError("Channel", channel_id)
        return ChannelResponse(**serialize_channel(doc))
