"""Common fixtures for Airtouch 5 tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.airtouch5.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry
