"""Tests for the Webmin integration."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.webmin.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .conftest import async_init_integration

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local anchor fixture (tryke discovery quirk)."""


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful unload of entry."""
    entry = await async_init_integration(hass)

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(bool(await hass.config_entries.async_unload(entry.entry_id))).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(bool(hass.data.get(DOMAIN))).to_be(False)


@test
async def entry_without_mac_address(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test an entry without MAC address."""
    entry = await async_init_integration(hass, False)

    expect(entry.runtime_data.unique_id).to_equal(entry.entry_id)
