"""Test init methods."""

from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from ._fixtures import (
    init_integration,
    mock_config_entry,
    mock_fibaro_client,
    mock_light,
    mock_room,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def unload_integration(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(mock_fibaro_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
    light: Mock = Depends(mock_light),
    room: Mock = Depends(mock_room),
) -> None:
    """Test unload integration stops state listener."""
    client.read_rooms.return_value = [room]
    client.read_devices.return_value = [light]

    with patch("homeassistant.components.fibaro.PLATFORMS", [Platform.LIGHT]):
        await init_integration(hass, entry)
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        expect(client.unregister_update_handler.call_count).to_equal(1)
