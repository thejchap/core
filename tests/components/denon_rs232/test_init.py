"""Tests for the Denon RS232 integration init."""

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import MockReceiver, init_components, mock_config_entry, mock_receiver

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def remove_entry_while_loaded(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_receiver: MockReceiver = Depends(mock_receiver),
    _components: None = Depends(init_components),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test removing a config entry does not schedule a reload."""
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_remove(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
    mock_receiver.disconnect.assert_awaited_once()
