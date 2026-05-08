"""Test Efergy integration."""

from pyefergy import exceptions
from tryke import Depends, expect, fixture, test

from homeassistant.components.efergy.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import _patch_efergy_status, create_entry, init_integration

from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test unload."""
    entry = await init_integration(hass, aioclient_mock)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(bool(hass.data.get(DOMAIN))).to_be(False)


@test
async def async_setup_entry_not_ready(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that it throws ConfigEntryNotReady when exception occurs during setup."""
    entry = create_entry(hass)
    with _patch_efergy_status() as efergymock:
        efergymock.side_effect = (exceptions.ConnectError, exceptions.DataError)
        await hass.config_entries.async_setup(entry.entry_id)
        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
        expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
        expect(bool(hass.data.get(DOMAIN))).to_be(False)


@test
async def async_setup_entry_auth_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that it throws ConfigEntryAuthFailed when authentication fails."""
    entry = create_entry(hass)
    with _patch_efergy_status() as efergymock:
        efergymock.side_effect = exceptions.InvalidAuth
        await hass.config_entries.async_setup(entry.entry_id)
        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
        expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)
        expect(bool(hass.data.get(DOMAIN))).to_be(False)


@test.skip("requires device_registry + setup_platform full sensor setup")
async def device_info() -> None:
    """Stub for test_device_info."""
