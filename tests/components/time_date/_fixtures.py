"""Tryke fixtures for Time & Date tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.time_date.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup
