"""Tests for the IOmeter integration."""

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock

from iometer import IOmeterConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.iometer import async_setup_entry
from homeassistant.components.iometer.const import DOMAIN
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from . import setup_platform
from ._fixtures import mock_config_entry, mock_iometer_client

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    freezer as freezer_fx,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def new_firmware_version(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    iometer_client: AsyncMock = Depends(mock_iometer_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    freezer: Any = Depends(freezer_fx),
) -> None:
    """Test device registry integration."""
    expect(config_entry.unique_id).not_.to_be(None)

    await setup_platform(hass, config_entry, [Platform.SENSOR])
    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, config_entry.unique_id)}
    )
    expect(device_entry).not_.to_be(None)
    expect(device_entry.sw_version).to_equal("build-58/build-65")
    iometer_client.get_current_status.return_value.device.core.version = "build-62"
    iometer_client.get_current_status.return_value.device.bridge.version = "build-69"
    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, config_entry.unique_id)}
    )
    expect(device_entry).not_.to_be(None)
    expect(device_entry.sw_version).to_equal("build-62/build-69")


@test
async def async_setup_entry_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    iometer_client: AsyncMock = Depends(mock_iometer_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test async_setup_entry raises ConfigEntryNotReady on connection error."""
    config_entry.add_to_hass(hass)
    iometer_client.get_current_status.side_effect = IOmeterConnectionError(
        "cannot connect"
    )

    async with expect_raises_async(ConfigEntryNotReady):
        await async_setup_entry(hass, config_entry)

    expect(iometer_client.get_current_status.await_count).to_equal(1)
