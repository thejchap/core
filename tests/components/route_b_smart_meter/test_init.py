"""Tests for the Smart Meter B Route integration init."""

from unittest.mock import Mock

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_momonga

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def async_setup_entry_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _momonga: Mock = Depends(mock_momonga),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test successful setup of entry."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
