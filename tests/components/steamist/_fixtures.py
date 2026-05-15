"""Tryke fixtures for the Steamist integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture


@fixture
def mock_aio_discovery() -> Generator[MagicMock]:
    """Mock AIODiscovery30303."""
    with patch(
        "homeassistant.components.steamist.discovery.AIODiscovery30303"
    ) as mock_aio_discovery:
        mock_aio_discovery.return_value.async_scan = AsyncMock()
        yield mock_aio_discovery
