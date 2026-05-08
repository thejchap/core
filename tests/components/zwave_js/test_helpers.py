"""Test the Z-Wave JS helpers module."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.zwave_js.helpers import (
    async_get_node_status_sensor_entity_id,
    async_get_nodes_from_area_id,
    format_home_id_for_display,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, device_registry as dr

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    area_registry as area_registry_fixture,
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture for tryke Depends() resolution."""
    return hass


@test
def format_home_id_for_display_returns_hex() -> None:
    """Test format_home_id_for_display."""
    expect(format_home_id_for_display(3245146787)).to_equal("0xc16d02a3")
    expect(format_home_id_for_display(0)).to_equal("0x00000000")
    expect(format_home_id_for_display(4294967295)).to_equal("0xffffffff")
    expect(format_home_id_for_display(None)).to_equal("Unknown")


@test
async def get_node_status_sensor_entity_id_for_non_zwave_js_device(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test async_get_node_status_sensor_entity_id for non zwave_js device."""
    config_entry = MockConfigEntry()
    config_entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={("test", "test")},
    )
    expect(async_get_node_status_sensor_entity_id(hass, device.id)).to_be(None)


@test
async def get_nodes_from_area_id_returns_empty(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
) -> None:
    """Test async_get_nodes_from_area_id returns empty for unknown area."""
    area = area_registry.async_create("test")
    expect(bool(async_get_nodes_from_area_id(hass, area.id))).to_be(False)


@test.skip("zwave_js: requires aeon_smart_switch_6 / client conftest fixtures")
async def get_value_state_schema_boolean_config_value() -> None:
    """Stub for test_get_value_state_schema_boolean_config_value."""


@test.skip("zwave_js: requires zwave_js client + ProvisioningEntry conftest fixtures")
async def async_get_provisioning_entry_from_device_id() -> None:
    """Stub for test_async_get_provisioning_entry_from_device_id."""
