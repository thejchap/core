"""Tests for analytics platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.analytics import async_devices_payload
from homeassistant.components.esphome import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor cross-module fixtures so tryke resolves before the test body."""
    return hass


@test
async def analytics(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test the analytics platform."""
    await async_setup_component(hass, "analytics", {})

    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={(DOMAIN, "test")},
        manufacturer="Test Manufacturer",
    )

    result = await async_devices_payload(hass)
    expect(DOMAIN not in result["integrations"]).to_be(True)
