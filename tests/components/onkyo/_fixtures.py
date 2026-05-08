"""Tryke fixtures for the Onkyo integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from . import RECEIVER_INFO, RECEIVER_INFO_2, mock_discovery


@fixture
def mock_default_discovery() -> Generator[None]:
    """Mock the discovery functions with default info (autouse equivalent)."""
    with (
        patch.multiple(
            "homeassistant.components.onkyo.receiver",
            DEVICE_INTERVIEW_TIMEOUT=1,
            DEVICE_DISCOVERY_TIMEOUT=1,
        ),
        mock_discovery([RECEIVER_INFO, RECEIVER_INFO_2]),
    ):
        yield


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock integration setup."""
    with patch(
        "homeassistant.components.onkyo.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry
