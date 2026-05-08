"""Tests for the Season integration."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.season.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def load_unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the Season configuration entry loading/unloading."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(bool(hass.data.get(DOMAIN))).to_be(False)
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
