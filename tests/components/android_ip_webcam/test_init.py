"""Tests for the Android IP Webcam integration."""

from unittest.mock import Mock

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant.components.android_ip_webcam.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import aioclient_mock_fixture

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_base,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import mock_async_zeroconf
from tests.test_util.aiohttp import AiohttpClientMocker

MOCK_CONFIG_DATA = {
    "name": "IP Webcam",
    "host": "1.1.1.1",
    "port": 8080,
    "username": "user",
    "password": "pass",
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test
async def successful_config_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _aiomock: None = Depends(aioclient_mock_fixture),
) -> None:
    """Test settings up integration from config entry."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_DATA)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)

    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def setup_failed_connection_error(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_base),
) -> None:
    """Test integration failed due to connection error."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_DATA)
    entry.add_to_hass(hass)
    aioclient_mock.get(
        "http://1.1.1.1:8080/status.json?show_avail=1",
        exc=aiohttp.ClientError,
    )

    await hass.config_entries.async_setup(entry.entry_id)

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def setup_failed_invalid_auth(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_base),
) -> None:
    """Test integration failed due to invalid auth."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_DATA)
    entry.add_to_hass(hass)
    aioclient_mock.get(
        "http://1.1.1.1:8080/status.json?show_avail=1",
        exc=aiohttp.ClientResponseError(Mock(), (), status=401),
    )

    await hass.config_entries.async_setup(entry.entry_id)

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _aiomock: None = Depends(aioclient_mock_fixture),
) -> None:
    """Test removing integration."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_DATA)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
