"""Tests for the LG Infrared integration setup."""

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import init_integration

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def setup_and_unload_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    init_integration: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test setting up and unloading a config entry."""
    entry = init_integration
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
