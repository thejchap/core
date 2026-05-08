"""Tryke fixtures for the energyid integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture


@fixture
def mock_polling_interval() -> Generator[int]:
    """Mock polling interval to 0 for faster tests."""
    with patch(
        "homeassistant.components.energyid.config_flow.POLLING_INTERVAL", new=0
    ) as polling_interval:
        yield polling_interval


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.energyid.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup
