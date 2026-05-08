"""Tests for Hydrawise devices."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.hydrawise.const import DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from ._fixtures import mock_pydrawise

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@fixture
async def mock_added_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    pydrawise: AsyncMock = Depends(mock_pydrawise),
) -> MockConfigEntry:
    """Mock ConfigEntry that's been added to HA."""
    entry = MockConfigEntry(
        title="Hydrawise",
        domain=DOMAIN,
        data={
            CONF_USERNAME: "asfd@asdf.com",
            CONF_PASSWORD: "__password__",
            CONF_API_KEY: "abc123",
        },
        unique_id="hydrawise-customerid",
        version=1,
        minor_version=2,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@test
async def zones_in_device_registry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    _entry: MockConfigEntry = Depends(mock_added_config_entry),
) -> None:
    """Test that zones are added to the device registry."""
    device1 = device_registry.async_get_device(identifiers={(DOMAIN, "5965394")})
    expect(device1).not_.to_be(None)
    expect(device1.name).to_equal("Zone One")
    expect(device1.manufacturer).to_equal("Hydrawise")

    device2 = device_registry.async_get_device(identifiers={(DOMAIN, "5965395")})
    expect(device2).not_.to_be(None)
    expect(device2.name).to_equal("Zone Two")
    expect(device2.manufacturer).to_equal("Hydrawise")


@test
async def controller_in_device_registry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    _entry: MockConfigEntry = Depends(mock_added_config_entry),
) -> None:
    """Test that the controller is added to the device registry."""
    device = device_registry.async_get_device(identifiers={(DOMAIN, "52496")})
    expect(device).not_.to_be(None)
    expect(device.name).to_equal("Home Controller")
    expect(device.manufacturer).to_equal("Hydrawise")
