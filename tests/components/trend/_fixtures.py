"""Tryke fixtures for the trend component tests."""

from collections.abc import Awaitable, Callable
from typing import Any

from tryke import Depends, fixture

from homeassistant.components.trend.config_flow import ConfigFlowHandler
from homeassistant.components.trend.const import DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)

type ComponentSetup = Callable[[dict[str, Any]], Awaitable[None]]


@fixture
def config_entry() -> MockConfigEntry:
    """Return a MockConfigEntry for testing."""
    return MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My trend",
            "entity_id": "sensor.cpu_temp",
            "invert": False,
            "max_samples": 2.0,
            "min_gradient": 0.0,
            "sample_duration": 0.0,
        },
        title="My trend",
    )


@fixture
async def setup_component(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> ComponentSetup:
    """Set up the trend component."""

    async def _setup_func(component_params: dict[str, Any]) -> None:
        config_entry.add_to_hass(hass)
        hass.config_entries.async_update_entry(
            config_entry,
            options={
                **config_entry.options,
                **component_params,
                "name": "test_trend_sensor",
                "entity_id": "sensor.test_state",
            },
            title="test_trend_sensor",
        )
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    return _setup_func


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
def trend_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_entry: er.RegistryEntry = Depends(sensor_entity_entry),
) -> MockConfigEntry:
    """Fixture to create a trend config entry."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My trend",
            "entity_id": entity_entry.entity_id,
            "invert": False,
        },
        title="My trend",
        version=ConfigFlowHandler.VERSION,
        minor_version=ConfigFlowHandler.MINOR_VERSION,
    )

    config_entry.add_to_hass(hass)

    return config_entry
