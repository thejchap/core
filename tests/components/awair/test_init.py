"""Test Awair init."""

from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from . import setup_awair
from ._fixtures import local_data, local_devices
from .const import LOCAL_CONFIG, LOCAL_UNIQUE_ID

from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import mock_async_zeroconf


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test
async def local_awair_sensors(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    local_devices: Any = Depends(local_devices),
    local_data: Any = Depends(local_data),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test expected sensors on a local Awair."""
    fixtures = [local_devices, local_data]
    entry = await setup_awair(hass, fixtures, LOCAL_UNIQUE_ID, LOCAL_CONFIG)

    device_entry = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

    expect(device_entry.name).to_equal("Mock Title")

    with patch("python_awair.AwairClient.query", side_effect=fixtures):
        hass.config_entries.async_update_entry(entry, title="Hello World")
        await hass.async_block_till_done()

    device_entry = device_registry.async_get(device_entry.id)
    expect(device_entry.name).to_equal("Hello World")
