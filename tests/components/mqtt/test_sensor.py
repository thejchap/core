"""The tests for the MQTT sensor platform."""

import copy
from typing import Any
from unittest.mock import patch

from tryke import Depends, fixture, test

from homeassistant.components import mqtt, sensor
from homeassistant.components.mqtt.sensor import MQTT_SENSOR_ATTRIBUTES_BLOCKED
from homeassistant.core import HomeAssistant

from ._fixtures import mqtt_mock as mqtt_mock_fixture
from .common import (
    help_test_discovery_broken,
    help_test_discovery_removal,
    help_test_discovery_update,
    help_test_discovery_update_attr,
    help_test_discovery_update_unchanged,
    help_test_entity_debug_info_message,
    help_test_entity_device_info_remove,
    help_test_entity_device_info_update,
    help_test_entity_device_info_with_connection,
    help_test_entity_device_info_with_identifier,
    help_test_entity_id_update_discovery_update,
    help_test_setting_blocked_attribute_via_mqtt_json_message,
)
from tests.hass_fixtures import (
    hass as hass_fixture,
    mock_network,
)

DEFAULT_CONFIG = {
    mqtt.DOMAIN: {sensor.DOMAIN: {"name": "test", "state_topic": "test-topic"}}
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _mqtt: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


def _make_mqtt_mock_entry(mqtt_mock: Any) -> Any:
    """Return a no-op coroutine returning ``mqtt_mock``.

    The original pytest ``mqtt_mock_entry`` fixture is a callable that sets
    up the MQTT integration on demand. In tryke the integration is set up
    eagerly by the ``mqtt_mock`` fixture in ``_fixtures.py``; this shim
    adapts the calling convention used by the ``help_test_*`` helpers.
    """

    async def _entry() -> Any:
        return mqtt_mock

    return _entry


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def setting_sensor_value_via_mqtt_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of the value via MQTT."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def setting_enum_sensor_value_via_mqtt_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of the enum sensor value via MQTT."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def handling_undecoded_sensor_value(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of undecoded value via MQTT."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def setting_sensor_to_long_state_via_mqtt_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setting sensor state to a too long state."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def setting_sensor_native_value_handling_via_mqtt_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of sensor native value handling via MQTT."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def setting_numeric_sensor_native_value_handling_via_mqtt_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of numeric sensor native value handling via MQTT."""
    _ = (hass, mqtt_mock)


@test.skip("requires freeze_time and parametrized hass_config")
async def setting_sensor_value_expires_availability_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the expiration of the value via MQTT with availability."""
    _ = (hass, mqtt_mock)


@test.skip("requires freeze_time and parametrized hass_config")
async def setting_sensor_value_expires(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the expiration of the value via MQTT."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def setting_sensor_value_via_mqtt_json_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of the value via MQTT with JSON payload."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def setting_sensor_value_via_mqtt_json_message_and_default_current_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of the value via MQTT with fall back to current state."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def setting_sensor_last_reset_via_mqtt_json_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of last_reset via MQTT JSON message."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def setting_sensor_last_reset_via_mqtt_json_message_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of last_reset via MQTT JSON message 2."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def force_update_disabled(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test force update option."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def force_update_enabled(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test force update option."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def availability_when_connection_lost(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test availability after MQTT disconnection."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def availability_without_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test availability without defined availability topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def default_availability_payload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test availability by default payload with defined topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def default_availability_list_payload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test availability by default payload with defined topic list."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def default_availability_list_payload_all(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test availability by default payload with defined topic list."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def default_availability_list_payload_any(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test availability by default payload with defined topic list."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def default_availability_list_single(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test availability with single non-list topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def custom_availability_payload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test availability by custom payload with defined topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def discovery_update_availability(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test update of discovered MQTTAvailability."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def invalid_device_class(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device_class option with invalid value."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def invalid_unit_of_measurement(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test invalid unit_of_measurement option."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def device_class_with_equivalent_unit_of_measurement_received(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of the value via MQTT for device class."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def equivalent_unit_of_measurement_received_without_device_class(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of the value via MQTT without device class."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def valid_device_class_and_uom(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test valid device_class and unit_of_measurement."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def invalid_state_class(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test invalid state_class option."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def invalid_state_class_with_unit_of_measurement(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test invalid state_class with unit_of_measurement."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def invalid_options_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test invalid options configuration."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def valid_state_class(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test valid state_class option."""
    _ = (hass, mqtt_mock)


@test.skip("attribute helper relies on entity created via mqtt_mock_entry config")
async def setting_attribute_via_mqtt_json_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of attribute via MQTT with JSON payload."""
    _ = (hass, mqtt_mock)


@test
async def setting_blocked_attribute_via_mqtt_json_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of blocked attribute via MQTT with JSON payload."""
    await help_test_setting_blocked_attribute_via_mqtt_json_message(
        hass,
        _make_mqtt_mock_entry(mqtt_mock),
        sensor.DOMAIN,
        DEFAULT_CONFIG,
        MQTT_SENSOR_ATTRIBUTES_BLOCKED,
    )


@test.skip("attribute helper relies on entity created via mqtt_mock_entry config")
async def setting_attribute_with_template(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of attribute via MQTT with JSON payload."""
    _ = (hass, mqtt_mock)


@test.skip("caplog fixture not available in tryke shim")
async def update_with_json_attrs_not_dict(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test attributes get extracted from a JSON result."""
    _ = (hass, mqtt_mock)


@test.skip("caplog fixture not available in tryke shim")
async def update_with_json_attrs_bad_json(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test attributes get extracted from a JSON result."""
    _ = (hass, mqtt_mock)


@test
async def discovery_update_attr(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test update of discovered MQTTAttributes."""
    await help_test_discovery_update_attr(
        hass, _make_mqtt_mock_entry(mqtt_mock), sensor.DOMAIN, DEFAULT_CONFIG
    )


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test unique id option only creates one sensor per unique_id."""
    _ = (hass, mqtt_mock)


@test
async def discovery_removal_sensor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test removal of discovered sensor."""
    data = '{ "name": "test", "state_topic": "test_topic" }'
    await help_test_discovery_removal(
        hass, _make_mqtt_mock_entry(mqtt_mock), sensor.DOMAIN, data
    )


@test
async def discovery_update_sensor_topic_template(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test update of discovered sensor."""
    config = {"name": "test", "state_topic": "test_topic"}
    config1 = copy.deepcopy(config)
    config2 = copy.deepcopy(config)
    config1["name"] = "Beer"
    config2["name"] = "Milk"
    config1["state_topic"] = "sensor/state1"
    config2["state_topic"] = "sensor/state2"
    config1["value_template"] = "{{ value_json.state | int }}"
    config2["value_template"] = "{{ value_json.state | int * 2 }}"

    state_data1 = [
        ([("sensor/state1", '{"state":100}')], "100", None),
    ]
    state_data2 = [
        ([("sensor/state1", '{"state":1000}')], "100", None),
        ([("sensor/state1", '{"state":1000}')], "100", None),
        ([("sensor/state2", '{"state":100}')], "200", None),
    ]

    await help_test_discovery_update(
        hass,
        _make_mqtt_mock_entry(mqtt_mock),
        sensor.DOMAIN,
        config1,
        config2,
        state_data1=state_data1,
        state_data2=state_data2,
    )


@test
async def discovery_update_sensor_template(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test update of discovered sensor."""
    config = {"name": "test", "state_topic": "test_topic"}
    config1 = copy.deepcopy(config)
    config2 = copy.deepcopy(config)
    config1["name"] = "Beer"
    config2["name"] = "Milk"
    config1["state_topic"] = "sensor/state1"
    config2["state_topic"] = "sensor/state1"
    config1["value_template"] = "{{ value_json.state | int }}"
    config2["value_template"] = "{{ value_json.state | int * 2 }}"

    state_data1 = [
        ([("sensor/state1", '{"state":100}')], "100", None),
    ]
    state_data2 = [
        ([("sensor/state1", '{"state":100}')], "200", None),
    ]

    await help_test_discovery_update(
        hass,
        _make_mqtt_mock_entry(mqtt_mock),
        sensor.DOMAIN,
        config1,
        config2,
        state_data1=state_data1,
        state_data2=state_data2,
    )


@test
async def discovery_update_unchanged_sensor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test update of discovered sensor."""
    data1 = '{ "name": "Beer", "state_topic": "test_topic" }'
    with patch(
        "homeassistant.components.mqtt.sensor.MqttSensor.discovery_update"
    ) as discovery_update:
        await help_test_discovery_update_unchanged(
            hass,
            _make_mqtt_mock_entry(mqtt_mock),
            sensor.DOMAIN,
            data1,
            discovery_update,
        )


@test
async def discovery_broken(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test handling of bad discovery message."""
    data1 = '{ "name": "Beer", "state_topic": "test_topic#" }'
    data2 = '{ "name": "Milk", "state_topic": "test_topic" }'
    await help_test_discovery_broken(
        hass, _make_mqtt_mock_entry(mqtt_mock), sensor.DOMAIN, data1, data2
    )


@test
async def entity_device_info_with_connection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT sensor device registry integration."""
    await help_test_entity_device_info_with_connection(
        hass, _make_mqtt_mock_entry(mqtt_mock), sensor.DOMAIN, DEFAULT_CONFIG
    )


@test
async def entity_device_info_with_identifier(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT sensor device registry integration."""
    await help_test_entity_device_info_with_identifier(
        hass, _make_mqtt_mock_entry(mqtt_mock), sensor.DOMAIN, DEFAULT_CONFIG
    )


@test
async def entity_device_info_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device registry update."""
    await help_test_entity_device_info_update(
        hass, _make_mqtt_mock_entry(mqtt_mock), sensor.DOMAIN, DEFAULT_CONFIG
    )


@test
async def entity_device_info_remove(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device registry remove."""
    await help_test_entity_device_info_remove(
        hass, _make_mqtt_mock_entry(mqtt_mock), sensor.DOMAIN, DEFAULT_CONFIG
    )


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def entity_id_update_subscriptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT subscriptions are managed when entity_id is updated."""
    _ = (hass, mqtt_mock)


@test
async def entity_id_update_discovery_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT discovery update when entity_id is updated."""
    await help_test_entity_id_update_discovery_update(
        hass, _make_mqtt_mock_entry(mqtt_mock), sensor.DOMAIN, DEFAULT_CONFIG
    )


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def entity_device_info_with_hub(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT sensor device registry integration with hub."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def entity_debug_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT sensor debug info."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def entity_debug_info_max_messages(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT sensor debug info."""
    _ = (hass, mqtt_mock)


@test
async def entity_debug_info_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT debug info."""
    await help_test_entity_debug_info_message(
        hass, _make_mqtt_mock_entry(mqtt_mock), sensor.DOMAIN, DEFAULT_CONFIG, None
    )


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def entity_debug_info_remove(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT sensor debug info."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def entity_debug_info_update_entity_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT sensor debug info."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def entity_disabled_by_default(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test entity disabled by default."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def entity_category(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test entity category."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def value_template_with_entity_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test value templates with entity_id."""
    _ = (hass, mqtt_mock)


@test.skip("requires mqtt_client_mock fixture for reloadable test")
async def reloadable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test reloading the MQTT platform."""
    _ = (hass, mqtt_mock)


@test.skip("requires mock_restore_cache_with_extra_data and parametrized hass_config")
async def cleanup_triggers_and_restoring_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test cleanup of state stored with last reset."""
    _ = (hass, mqtt_mock)


@test.skip("requires mock_restore_cache_with_extra_data and parametrized hass_config")
async def skip_restoring_state_with_over_due_expire_trigger(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test skipping restore of state when expire trigger has fired."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def encoding_subscribable_topics(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test handling of incoming encoded payload."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def setup_manual_entity_from_yaml(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setup manual configured MQTT entity."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test unloading the config entry."""
    _ = (hass, mqtt_mock)


@test.skip("requires parametrized expected_friendly_name/device_class combos")
async def entity_name(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the entity name setup."""
    _ = (hass, mqtt_mock)


@test.skip("entity icon/picture helper relies on mqtt_mock_entry YAML setup")
async def entity_icon_and_entity_picture(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the entity icon or picture setup."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def skipped_async_ha_write_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test skipping write state."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config")
async def value_template_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test value template that fails."""
    _ = (hass, mqtt_mock)


@test.skip("requires issue_registry and parametrized hass_config")
async def value_incorrect_state_class_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test value with incorrect state class config."""
    _ = (hass, mqtt_mock)
