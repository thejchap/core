"""Test init for Snoo."""

from unittest.mock import AsyncMock

from python_snoo.exceptions import SnooAuthException
from tryke import Depends, expect, fixture, test

from homeassistant.components.snoo import SnooDeviceError
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import async_init_integration
from ._fixtures import bypass_api

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def async_setup_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _bypass: AsyncMock = Depends(bypass_api),
) -> None:
    """Test a successful setup entry."""
    entry = await async_init_integration(hass)
    expect(len(hass.states.async_all("sensor"))).to_equal(2)
    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def cannot_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    bypass: AsyncMock = Depends(bypass_api),
) -> None:
    """Test that we are put into retry when we fail to auth."""
    bypass.authorize.side_effect = SnooAuthException
    entry = await async_init_integration(hass)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def failed_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    bypass: AsyncMock = Depends(bypass_api),
) -> None:
    """Test that we are put into retry when we fail to get devices."""
    bypass.get_devices.side_effect = SnooDeviceError
    entry = await async_init_integration(hass)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
