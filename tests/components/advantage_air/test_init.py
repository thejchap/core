"""Test the Advantage Air Initialization."""

from unittest.mock import AsyncMock

from advantage_air import ApiError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import add_mock_config, patch_get
from ._fixtures import mock_get

from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import mock_async_zeroconf


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test
async def async_setup_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_get: AsyncMock = Depends(mock_get),
) -> None:
    """Test a successful setup entry and unload."""
    entry = await add_mock_config(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def async_setup_entry_failure(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a unsuccessful setup entry."""
    with patch_get(side_effect=ApiError):
        entry = await add_mock_config(hass)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
