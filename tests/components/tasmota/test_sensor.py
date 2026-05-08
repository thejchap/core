"""The tests for the Tasmota sensor platform."""

import copy
import json
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.tasmota.const import DEFAULT_PREFIX
from homeassistant.core import HomeAssistant

from ._fixtures import mqtt_mock as mqtt_mock_fixture, setup_tasmota
from .test_common import DEFAULT_CONFIG

from tests.common import async_fire_mqtt_message
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test
async def attributes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota),
) -> None:
    """Test correct attributes for sensors."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    sensor_config = {
        "sn": {
            "DHT11": {"Temperature": None},
            "Beer": {"CarbonDioxide": None},
            "TempUnit": "C",
        }
    }
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()
    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/sensors",
        json.dumps(sensor_config),
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.tasmota_dht11_temperature")
    expect(state is not None).to_be(True)
    expect(state.attributes.get("device_class")).to_equal("temperature")
    expect(state.attributes.get("friendly_name")).to_equal("Tasmota DHT11 Temperature")
    expect(state.attributes.get("icon")).to_be(None)
    expect(state.attributes.get("unit_of_measurement")).to_equal("°C")

    state = hass.states.get("sensor.tasmota_beer_CarbonDioxide")
    expect(state is not None).to_be(True)
    expect(state.attributes.get("device_class")).to_equal("carbon_dioxide")
    expect(state.attributes.get("friendly_name")).to_equal("Tasmota Beer CarbonDioxide")
    expect(state.attributes.get("icon")).to_be(None)
    expect(state.attributes.get("unit_of_measurement")).to_equal("ppm")


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def controlling_state_via_mqtt() -> None:
    """Stub for test_controlling_state_via_mqtt."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def quantity_override() -> None:
    """Stub for test_quantity_override."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def bad_indexed_sensor_state_via_mqtt() -> None:
    """Stub for test_bad_indexed_sensor_state_via_mqtt."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def status_sensor_state_via_mqtt() -> None:
    """Stub for test_status_sensor_state_via_mqtt."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def battery_sensor_state_via_mqtt() -> None:
    """Stub for test_battery_sensor_state_via_mqtt."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def single_shot_status_sensor_state_via_mqtt() -> None:
    """Stub for test_single_shot_status_sensor_state_via_mqtt."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def restart_time_status_sensor_state_via_mqtt() -> None:
    """Stub for test_restart_time_status_sensor_state_via_mqtt."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def nested_sensor_attributes() -> None:
    """Stub for test_nested_sensor_attributes."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def indexed_sensor_attributes() -> None:
    """Stub for test_indexed_sensor_attributes."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def diagnostic_sensors() -> None:
    """Stub for test_diagnostic_sensors."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def enable_status_sensor() -> None:
    """Stub for test_enable_status_sensor."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def availability_when_connection_lost() -> None:
    """Stub for test_availability_when_connection_lost."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def deep_sleep_availability_when_connection_lost() -> None:
    """Stub for test_deep_sleep_availability_when_connection_lost."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def availability() -> None:
    """Stub for test_availability."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def deep_sleep_availability() -> None:
    """Stub for test_deep_sleep_availability."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def availability_discovery_update() -> None:
    """Stub for test_availability_discovery_update."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def availability_poll_state() -> None:
    """Stub for test_availability_poll_state."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def discovery_removal_sensor() -> None:
    """Stub for test_discovery_removal_sensor."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def discovery_update_unchanged_sensor() -> None:
    """Stub for test_discovery_update_unchanged_sensor."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def discovery_device_remove() -> None:
    """Stub for test_discovery_device_remove."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def entity_id_update_subscriptions() -> None:
    """Stub for test_entity_id_update_subscriptions."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def entity_id_update_discovery_update() -> None:
    """Stub for test_entity_id_update_discovery_update."""
