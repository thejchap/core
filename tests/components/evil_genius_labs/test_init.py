"""Test evil genius labs init."""

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import config_entry, setup_evil_genius_labs

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def setup_unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_evil_genius_labs),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test setting up and unloading a config entry."""
    expect(len(hass.states.async_entity_ids())).to_equal(1)
    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
