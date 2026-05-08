"""Module contains tests for the ekeybionyx component's initialization."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.ekeybionyx.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import config_entry as config_entry_fixture

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Tryke discovery anchor."""


@test
async def async_setup_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test a successful setup entry and unload of entry."""
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
