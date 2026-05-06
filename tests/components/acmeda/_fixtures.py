"""Tryke fixtures for the Acmeda integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture


@fixture
def mock_hub_run() -> Generator[AsyncMock]:
    """Mock the hub run method."""
    with patch("homeassistant.components.acmeda.hub.aiopulse.Hub.run") as mock_run:
        yield mock_run


@fixture
def mock_hub_discover() -> Generator[object]:
    """Mock the hub discover method."""
    with patch("aiopulse.Hub.discover") as mock_discover:
        yield mock_discover
