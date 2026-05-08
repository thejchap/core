"""Tests for the MJPEG IP Camera integration."""

from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.mjpeg.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_mjpeg_requests

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local fixture anchor."""


@test
async def load_unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _mjpeg: MagicMock = Depends(mock_mjpeg_requests),
) -> None:
    """Test the MJPEG IP Camera configuration entry loading/unloading."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    expect(bool(hass.data.get(DOMAIN))).to_be(False)
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.skip("test_reload_config_entry depends on mock_reload_entry/init_integration fixtures not in shim")
async def reload_config_entry() -> None:
    """Stub for test_reload_config_entry (port deferred)."""
