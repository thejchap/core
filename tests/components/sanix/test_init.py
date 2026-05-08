"""Test the Sanix init module."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_config_entry, mock_sanix

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def load_unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _sanix: MagicMock = Depends(mock_sanix),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test load and unload entry."""
    await setup_integration(hass, config_entry)

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
