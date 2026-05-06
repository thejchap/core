"""Tryke fixtures for speedtestdotnet tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import fixture

from . import MOCK_SERVERS


@fixture
def mock_setup_entry() -> Generator[MagicMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.speedtestdotnet.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_api() -> Generator[MagicMock]:
    """Mock entry setup."""
    with patch("speedtest.Speedtest") as mock_api:
        mock_api.return_value.get_servers.return_value = MOCK_SERVERS
        yield mock_api
