"""Tryke fixtures for National Weather Service tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture


@fixture
def mock_simple_nws_config() -> Generator[MagicMock]:
    """Mock pynws SimpleNWS with default values in config_flow."""
    with patch("homeassistant.components.nws.config_flow.SimpleNWS") as mock_nws:
        instance = mock_nws.return_value
        instance.set_station = AsyncMock(return_value=None)
        instance.station = "ABC"
        instance.stations = ["ABC"]
        yield mock_nws
