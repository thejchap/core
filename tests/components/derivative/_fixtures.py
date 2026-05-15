"""Tryke fixtures for derivative tests."""

from tryke import Depends, fixture

from homeassistant.components.derivative.config_flow import ConfigFlowHandler
from homeassistant.components.derivative.const import DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)


@fixture
def sensor_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Fixture to create a sensor config entry."""
    sensor_config_entry = MockConfigEntry()
    sensor_config_entry.add_to_hass(hass)
    return sensor_config_entry


@fixture
def sensor_device(
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    config_entry: ConfigEntry = Depends(sensor_config_entry),
) -> dr.DeviceEntry:
    """Fixture to create a sensor device."""
    return device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )


@fixture
def sensor_entity_entry(
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    config_entry: ConfigEntry = Depends(sensor_config_entry),
    device: dr.DeviceEntry = Depends(sensor_device),
) -> er.RegistryEntry:
    """Fixture to create a sensor entity entry."""
    return entity_registry.async_get_or_create(
        "sensor",
        "test",
        "unique",
        config_entry=config_entry,
        device_id=device.id,
        original_name="ABC",
    )


@fixture
def derivative_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_entry: er.RegistryEntry = Depends(sensor_entity_entry),
) -> MockConfigEntry:
    """Fixture to create a derivative config entry."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My derivative",
            "round": 1.0,
            "source": entity_entry.entity_id,
            "time_window": {"seconds": 0.0},
            "unit_prefix": "k",
            "unit_time": "min",
        },
        title="My derivative",
        version=ConfigFlowHandler.VERSION,
        minor_version=ConfigFlowHandler.MINOR_VERSION,
    )

    config_entry.add_to_hass(hass)

    return config_entry
