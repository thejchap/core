"""The tests for the Canary component."""

from unittest.mock import MagicMock

from requests import ConnectTimeout
from tryke import Depends, expect, fixture, test

from homeassistant.components.canary.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import init_integration
from ._fixtures import canary, mock_ffmpeg

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _ffmpeg: None = Depends(mock_ffmpeg),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def unload_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    canary: MagicMock = Depends(canary),
) -> None:
    """Test successful unload of entry."""
    entry = await init_integration(hass)

    expect(entry).not_.to_be(None)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(bool(hass.data.get(DOMAIN))).to_be(False)


@test
async def async_setup_raises_entry_not_ready(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    canary: MagicMock = Depends(canary),
) -> None:
    """Test that it throws ConfigEntryNotReady when exception occurs during setup."""
    canary.side_effect = ConnectTimeout()

    entry = await init_integration(hass)
    expect(entry).not_.to_be(None)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
