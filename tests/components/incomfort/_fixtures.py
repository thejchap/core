"""Tryke fixtures for the incomfort integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.incomfort.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_incomfort() -> Generator[MagicMock]:
    """Mock the InComfort gateway client (minimal: heater list)."""
    mock_heater = MagicMock()
    mock_heater.serial_no = "c0ffeec0ffee"

    with patch(
        "homeassistant.components.incomfort.coordinator.InComfortGateway", MagicMock()
    ) as patch_gateway:
        patch_gateway().heaters = AsyncMock()
        patch_gateway().heaters.return_value = [mock_heater]
        yield patch_gateway
