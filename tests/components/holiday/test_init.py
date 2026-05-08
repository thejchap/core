"""Tests for the Holiday integration."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.holiday.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

MOCK_CONFIG_DATA = {
    "country": "Germany",
    "province": "BW",
}


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def unload_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test removing integration."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_DATA)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    state: ConfigEntryState = entry.state
    expect(state).to_be(ConfigEntryState.NOT_LOADED)
