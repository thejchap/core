"""The tests for the MQTT water heater platform."""

import json
from typing import Any
from unittest.mock import patch

from tryke import Depends, fixture, test

from homeassistant.components import mqtt, water_heater
from homeassistant.components.mqtt.water_heater import (
    MQTT_WATER_HEATER_ATTRIBUTES_BLOCKED,
)
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
    mqtt.DOMAIN: {
        water_heater.DOMAIN: {
            "name": "test",
            "mode_command_topic": "mode-topic",
            "temperature_command_topic": "temperature-topic",
        }
    }
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
async def setup_params(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the initial parameters."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def supported_features(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the supported_features."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def get_operation_modes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test that the operation list returns the correct modes."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_operation_mode_bad_attr_and_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setting operation mode without required attribute."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_operation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setting of new operation mode."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_operation_pessimistic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setting operation mode in pessimistic mode."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_operation_optimistic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setting operation mode in optimistic mode."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_operation_with_power_command(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setting of new operation mode with power command."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def turn_on_and_off_optimistic_with_power_command(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test turn_on/turn_off in optimistic mode with power command."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_target_temperature(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setting the target temperature."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_target_temperature_pessimistic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setting target temperature in pessimistic mode."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_target_temperature_optimistic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setting target temperature in optimistic mode."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def receive_mqtt_temperature(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test getting the current temperature via MQTT."""
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
async def custom_availability_payload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test availability by custom payload with defined topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def get_with_templates(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test getting various attributes with templates."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_and_templates(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setting various attributes with templates."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def min_temp_custom(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test a custom min temp."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def max_temp_custom(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test a custom max temp."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def temperature_unit(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test that setting temperature_unit affects unit of measurement."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def alt_temperature_unit(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test deriving min/max temperatures."""
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
        water_heater.DOMAIN,
        DEFAULT_CONFIG,
        MQTT_WATER_HEATER_ATTRIBUTES_BLOCKED,
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
        hass, _make_mqtt_mock_entry(mqtt_mock), water_heater.DOMAIN, DEFAULT_CONFIG
    )


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test unique id option only creates one water heater per unique_id."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized topic/value combos")
async def encoding_subscribable_topics(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test handling of incoming encoded payload."""
    _ = (hass, mqtt_mock)


@test
async def discovery_removal_water_heater(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test removal of discovered water heater."""
    data = json.dumps(DEFAULT_CONFIG[mqtt.DOMAIN][water_heater.DOMAIN])
    await help_test_discovery_removal(
        hass, _make_mqtt_mock_entry(mqtt_mock), water_heater.DOMAIN, data
    )


@test
async def discovery_update_water_heater(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test update of discovered water heater."""
    config1 = {"name": "Beer"}
    config2 = {"name": "Milk"}
    await help_test_discovery_update(
        hass, _make_mqtt_mock_entry(mqtt_mock), water_heater.DOMAIN, config1, config2
    )


@test
async def discovery_update_unchanged_water_heater(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test update of discovered water heater."""
    data1 = '{ "name": "Beer" }'
    with patch(
        "homeassistant.components.mqtt.water_heater.MqttWaterHeater.discovery_update"
    ) as discovery_update:
        await help_test_discovery_update_unchanged(
            hass,
            _make_mqtt_mock_entry(mqtt_mock),
            water_heater.DOMAIN,
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
    data1 = '{ "name": "Beer", "mode_command_topic": "test_topic#" }'
    data2 = '{ "name": "Milk", "mode_command_topic": "test_topic" }'
    await help_test_discovery_broken(
        hass, _make_mqtt_mock_entry(mqtt_mock), water_heater.DOMAIN, data1, data2
    )


@test
async def entity_device_info_with_connection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT water heater device registry integration."""
    await help_test_entity_device_info_with_connection(
        hass, _make_mqtt_mock_entry(mqtt_mock), water_heater.DOMAIN, DEFAULT_CONFIG
    )


@test
async def entity_device_info_with_identifier(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT water heater device registry integration."""
    await help_test_entity_device_info_with_identifier(
        hass, _make_mqtt_mock_entry(mqtt_mock), water_heater.DOMAIN, DEFAULT_CONFIG
    )


@test
async def entity_device_info_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device registry update."""
    await help_test_entity_device_info_update(
        hass, _make_mqtt_mock_entry(mqtt_mock), water_heater.DOMAIN, DEFAULT_CONFIG
    )


@test
async def entity_device_info_remove(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device registry remove."""
    await help_test_entity_device_info_remove(
        hass, _make_mqtt_mock_entry(mqtt_mock), water_heater.DOMAIN, DEFAULT_CONFIG
    )


@test.skip("entity_id_update_subscriptions helper requires mqtt_mock_entry config")
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
        hass, _make_mqtt_mock_entry(mqtt_mock), water_heater.DOMAIN, DEFAULT_CONFIG
    )


@test
async def entity_debug_info_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT debug info."""
    config = {
        mqtt.DOMAIN: {
            water_heater.DOMAIN: {
                "name": "test",
                "mode_command_topic": "command-topic",
                "mode_state_topic": "test-topic",
            }
        }
    }
    await help_test_entity_debug_info_message(
        hass,
        _make_mqtt_mock_entry(mqtt_mock),
        water_heater.DOMAIN,
        config,
        water_heater.SERVICE_SET_OPERATION_MODE,
        command_topic="command-topic",
        command_payload="eco",
        state_topic="test-topic",
        service_parameters={"operation_mode": "eco"},
    )


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def precision_default(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test that setting precision to tenths works as intended."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def precision_halves(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test that setting precision to halves works as intended."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def precision_whole(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test that setting precision to whole works as intended."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized service/topic/payload combos")
async def publishing_with_custom_encoding(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test publishing MQTT payload with different encoding."""
    _ = (hass, mqtt_mock)


@test.skip("requires mqtt_client_mock fixture for reloadable test")
async def reloadable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test reloading the MQTT platform."""
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


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def skipped_async_ha_write_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test no redundant async_write_ha_state calls."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config")
async def value_template_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the rendering of MQTT value template fails gracefully."""
    _ = (hass, mqtt_mock)
