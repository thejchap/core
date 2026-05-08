"""Test the flume init."""

from collections.abc import Generator
from unittest.mock import patch

import requests_mock
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from ._fixtures import (
    access_token,
    config_entry,
    device_list,
    device_list_timeout,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@fixture
def platforms_fixture() -> Generator[None]:
    """Return the platforms to be loaded for this test."""
    with patch("homeassistant.components.flume.PLATFORMS", [Platform.BINARY_SENSOR]):
        yield


@test
async def setup_config_entry(
    _trigger: None = Depends(_trigger_executor),
    _platforms: None = Depends(platforms_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    _token: None = Depends(access_token),
    _devices: None = Depends(device_list),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test load and unload of a ConfigEntry."""
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(config_entries.ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    expect(entry.state).to_be(config_entries.ConfigEntryState.NOT_LOADED)


@test
async def device_list_timeout_test(
    _trigger: None = Depends(_trigger_executor),
    _platforms: None = Depends(platforms_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    _token: None = Depends(access_token),
    _timeout: None = Depends(device_list_timeout),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test error handling for a timeout when listing devices."""
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(False)
    await hass.async_block_till_done()

    expect(entry.state).to_be(config_entries.ConfigEntryState.SETUP_RETRY)


@test.skip("requires device_list_unauthorized fixture")
async def reauth_when_unauthorized() -> None:
    """Stub for test_reauth_when_unauthorized."""


@test.skip("requires notifications_list fixture + service call")
async def list_notifications_service() -> None:
    """Stub for test_list_notifications_service."""


@test.skip("requires notifications_list fixture + service call")
async def list_notifications_service_no_response() -> None:
    """Stub for test_list_notifications_service_no_response."""
