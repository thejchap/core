"""The tests for the MQTT cover platform."""

from typing import Any
from unittest.mock import patch

from tryke import Depends, fixture, test

from homeassistant.components import cover, mqtt
from homeassistant.components.mqtt.cover import MQTT_COVER_ATTRIBUTES_BLOCKED
from homeassistant.const import SERVICE_OPEN_COVER
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
    mqtt.DOMAIN: {cover.DOMAIN: {"name": "test", "state_topic": "test-topic"}}
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
async def state_via_state_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the controlling state via topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def opening_and_closing_state_via_custom_state_payload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test opening/closing state via custom payload."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def open_closed_state_from_position_optimistic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test open/closed state from position when optimistic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def open_closed_state_from_position_optimistic_alt_positions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test open/closed state from position alt positions when optimistic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_open_closed_toggle_optimistic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt open/closed toggle when optimistic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_open_closed_toggle_optimistic_alt_positions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt open/closed toggle alt positions when optimistic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def position_via_position_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test position via position topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def state_via_template(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the controlling state via topic with template."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def state_via_template_and_entity_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the controlling state via topic with template and entity id."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def state_via_template_with_json_value(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the controlling state via topic with template and JSON value."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def position_via_template_and_entity_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test position via template using entity id."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def optimistic_flag(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test optimistic flag."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def optimistic_state_change(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test optimistic state change."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def optimistic_state_change_with_position(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test optimistic state change with position."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def send_open_cover_command(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the sending of open_cover command."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def send_close_cover_command(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the sending of close_cover command."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def send_stop_cover_command(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the sending of stop_cover command."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def send_stop_tilt_command(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the sending of stop_cover_tilt command."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def current_cover_position(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setting the current cover position."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def current_cover_position_inverted(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setting the current cover position inverted."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def optimistic_position(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test optimistic position."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def position_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test position update."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_position_templated(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test set position templated."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_position_templated_and_attributes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test set position templated using template attributes."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_tilt_templated(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test set tilt templated."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_tilt_templated_and_attributes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test set tilt templated using template attributes."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_position_untemplated(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test set position untemplated."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_position_untemplated_custom_percentage_range(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test set position untemplated with custom range."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def no_command_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test no command topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def no_payload_close(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test no payload close."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def no_payload_open(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test no payload open."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def no_payload_stop(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test no payload stop."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def with_command_topic_and_tilt(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test with command topic and tilt."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_defaults(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt defaults."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_via_invocation_defaults(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt via invocation defaults."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_given_value(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt given value."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_given_value_optimistic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt given value optimistic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_given_value_altered_range(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt given value altered range."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_via_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt via topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_via_topic_template(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt via topic template."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_via_topic_template_json_value(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt via topic template with JSON value."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_via_topic_altered_range(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt via topic altered range."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config")
async def tilt_status_out_of_range_warning(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt status out of range warning."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config")
async def tilt_status_not_numeric_warning(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt status not numeric warning."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_via_topic_altered_range_inverted(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt via topic altered range inverted."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_via_topic_template_altered_range(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt via topic template altered range."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_position(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt position."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_position_templated(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt position templated."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def tilt_position_altered_range(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt position altered range."""
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
async def valid_device_class(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of a valid device class."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config")
async def invalid_device_class(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of an invalid device class."""
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
        cover.DOMAIN,
        DEFAULT_CONFIG,
        MQTT_COVER_ATTRIBUTES_BLOCKED,
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
        hass, _make_mqtt_mock_entry(mqtt_mock), cover.DOMAIN, DEFAULT_CONFIG
    )


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test unique_id option only creates one cover per id."""
    _ = (hass, mqtt_mock)


@test
async def discovery_removal_cover(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test removal of discovered cover."""
    data = '{ "name": "test", "command_topic": "test_topic" }'
    await help_test_discovery_removal(
        hass, _make_mqtt_mock_entry(mqtt_mock), cover.DOMAIN, data
    )


@test
async def discovery_update_cover(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test update of discovered cover."""
    config1 = {"name": "Beer", "command_topic": "test_topic"}
    config2 = {"name": "Milk", "command_topic": "test_topic"}
    await help_test_discovery_update(
        hass, _make_mqtt_mock_entry(mqtt_mock), cover.DOMAIN, config1, config2
    )


@test
async def discovery_update_unchanged_cover(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test update of discovered cover."""
    data1 = '{ "name": "Beer", "command_topic": "test_topic" }'
    with patch(
        "homeassistant.components.mqtt.cover.MqttCover.discovery_update"
    ) as discovery_update:
        await help_test_discovery_update_unchanged(
            hass,
            _make_mqtt_mock_entry(mqtt_mock),
            cover.DOMAIN,
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
    data1 = '{ "name": "Beer", "command_topic": "test_topic#" }'
    data2 = '{ "name": "Milk", "command_topic": "test_topic" }'
    await help_test_discovery_broken(
        hass, _make_mqtt_mock_entry(mqtt_mock), cover.DOMAIN, data1, data2
    )


@test
async def entity_device_info_with_connection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT cover device registry integration."""
    await help_test_entity_device_info_with_connection(
        hass, _make_mqtt_mock_entry(mqtt_mock), cover.DOMAIN, DEFAULT_CONFIG
    )


@test
async def entity_device_info_with_identifier(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT cover device registry integration."""
    await help_test_entity_device_info_with_identifier(
        hass, _make_mqtt_mock_entry(mqtt_mock), cover.DOMAIN, DEFAULT_CONFIG
    )


@test
async def entity_device_info_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device registry update."""
    await help_test_entity_device_info_update(
        hass, _make_mqtt_mock_entry(mqtt_mock), cover.DOMAIN, DEFAULT_CONFIG
    )


@test
async def entity_device_info_remove(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device registry remove."""
    await help_test_entity_device_info_remove(
        hass, _make_mqtt_mock_entry(mqtt_mock), cover.DOMAIN, DEFAULT_CONFIG
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
        hass, _make_mqtt_mock_entry(mqtt_mock), cover.DOMAIN, DEFAULT_CONFIG
    )


@test
async def entity_debug_info_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT debug info."""
    await help_test_entity_debug_info_message(
        hass,
        _make_mqtt_mock_entry(mqtt_mock),
        cover.DOMAIN,
        DEFAULT_CONFIG,
        SERVICE_OPEN_COVER,
        command_payload="OPEN",
    )


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def state_and_position_topics_state_not_set_via_position_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test state is not set via position topic when both state and position are set."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_state_via_position_using_stopped_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setting state via position using stopped state."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def position_via_position_topic_template(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test position via position topic template."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def position_via_position_topic_template_json_value(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test position via position topic template with JSON value."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def position_template_with_entity_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test position template with entity id."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def position_via_position_topic_template_return_json(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test position via topic template returning JSON."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config")
async def position_via_position_topic_template_return_json_warning(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test position via topic template returning JSON warning."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def position_and_tilt_via_position_topic_template_return_json(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test position and tilt via topic template returning JSON."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def position_via_position_topic_template_all_variables(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test position via topic template using all variables."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def set_state_via_stopped_state_no_position_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test set state via stopped state no position topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config")
async def position_via_position_topic_template_return_invalid_json(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test position via topic template returning invalid JSON."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config")
async def set_position_topic_without_get_position_topic_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test set position topic without get position topic raises error."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config")
async def value_template_without_state_topic_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test value template without state topic raises error."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config")
async def position_template_without_position_topic_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test position template without position topic raises error."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config")
async def set_position_template_without_set_position_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test set position template without set position topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config")
async def tilt_command_template_without_tilt_command_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt command template without tilt command topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config")
async def tilt_status_template_without_tilt_status_topic_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test tilt status template without tilt status topic."""
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


@test.skip("requires caplog and parametrized topic/value combos")
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


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def entity_icon_and_entity_picture(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test entity icon and entity picture."""
    _ = (hass, mqtt_mock)
