"""Tests for the TechnoVE integration."""

from unittest.mock import MagicMock

from technove import TechnoVEConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import init_integration, mock_config_entry, mock_technove

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local anchor fixture (tryke discovery quirk)."""


@test
async def async_setup_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test a successful setup entry and unload."""
    entry.add_to_hass(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(bool(await hass.config_entries.async_unload(entry.entry_id))).to_be(True)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def async_setup_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    technove: MagicMock = Depends(mock_technove),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test a connection error after setup."""
    technove.update.side_effect = TechnoVEConnectionError
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
