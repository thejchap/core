"""Tests for the ATAG integration."""

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import init_integration, mock_connection
from ._fixtures import mock_pyatag_sleep

from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import mock_async_zeroconf
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
    _sleep: None = Depends(mock_pyatag_sleep),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test
async def config_entry_not_ready(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test configuration entry not ready on library error."""
    mock_connection(aioclient_mock, conn_error=True)
    entry = await init_integration(hass, aioclient_mock)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_config_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test the ATAG configuration entry unloading."""
    entry = await init_integration(hass, aioclient_mock)
    expect(bool(entry.runtime_data)).to_be(True)
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    expect(hasattr(entry, "runtime_data")).to_be(False)
