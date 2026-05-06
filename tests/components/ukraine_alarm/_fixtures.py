"""Tryke fixtures for the Ukraine Alarm config flow tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from . import REGIONS


@fixture
def mock_get_regions() -> Generator[AsyncMock]:
    """Mock the get_regions method."""
    with patch(
        "homeassistant.components.ukraine_alarm.config_flow.Client.get_regions",
        return_value=REGIONS,
    ) as mock_get:
        yield mock_get
