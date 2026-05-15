"""Tests for analytics platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.analytics import async_devices_payload
from homeassistant.components.mobile_app import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component

from ._fixtures import setup_ws as setup_ws_fixture

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def analytics(
    _trigger: None = Depends(_trigger_executor),
    _ws: None = Depends(setup_ws_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
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
