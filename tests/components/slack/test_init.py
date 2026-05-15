"""Test Slack integration."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.slack.const import DOMAIN
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant

from . import CONF_DATA, async_init_integration

from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def setup(
    hass: HomeAssistant = Depends(_trigger_executor),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test Slack setup."""
    entry: ConfigEntry = await async_init_integration(hass, aioclient_mock)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.data).to_equal(CONF_DATA)


@test
async def async_setup_entry_not_ready(
    hass: HomeAssistant = Depends(_trigger_executor),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that it throws ConfigEntryNotReady when exception occurs during setup."""
    entry: ConfigEntry = await async_init_integration(
        hass, aioclient_mock, error="cannot_connect"
    )
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def async_setup_entry_invalid_auth(
    hass: HomeAssistant = Depends(_trigger_executor),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test invalid auth during setup."""
    entry: ConfigEntry = await async_init_integration(
        hass, aioclient_mock, error="invalid_auth"
    )
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)
