"""Tests for the Rhasspy integration."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.rhasspy.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def load_unload_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the Rhasspy configuration entry loading/unloading."""
    mock_config_entry = MockConfigEntry(
        title="Rhasspy",
        domain=DOMAIN,
        data={},
    )
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(hass.data.get(DOMAIN)).to_be_falsy()
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
