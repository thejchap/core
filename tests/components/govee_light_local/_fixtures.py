"""Tryke fixtures for Govee Local API tests."""

from asyncio import Event
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from homeassistant.components.govee_light_local.coordinator import GoveeController


@fixture
def mock_govee_api() -> Generator[AsyncMock]:
    """Set up Govee Local API fixture."""
    mock_api = AsyncMock(spec=GoveeController)
    mock_api.start = AsyncMock()
    mock_api.cleanup = MagicMock(return_value=Event())
    mock_api.cleanup.return_value.set()
    mock_api.turn_on_off = AsyncMock()
    mock_api.set_brightness = AsyncMock()
    mock_api.set_color = AsyncMock()
    mock_api.set_scene = AsyncMock()
    mock_api._async_update_data = AsyncMock()

    with (
        patch(
            "homeassistant.components.govee_light_local.coordinator.GoveeController",
            return_value=mock_api,
        ) as mock_controller,
        patch(
            "homeassistant.components.govee_light_local.config_flow.GoveeController",
            return_value=mock_api,
        ),
    ):
        yield mock_controller.return_value


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.govee_light_local.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry
