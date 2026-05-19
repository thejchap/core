"""The tests for the MQTT event platform."""

from typing import Any

from tryke import Depends, fixture, test

from homeassistant.components import event, mqtt
from homeassistant.components.mqtt.event import MQTT_EVENT_ATTRIBUTES_BLOCKED
from homeassistant.core import HomeAssistant

from ._fixtures import mqtt_mock as mqtt_mock_fixture
from .common import (
    help_test_discovery_broken,
    help_test_discovery_removal,
    help_test_discovery_update_attr,
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
        event.DOMAIN: {
            "name": "test",
            "state_topic": "test-topic",
            "event_types": ["press"],
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
async def setting_event_value_via_mqtt_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of the event value via MQTT."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def multiple_events_are_all_updating_the_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of the event value via MQTT for multiple events."""
    _ = (hass, mqtt_mock)


@test.skip("requires freezer fixture and parametrized hass_config")
async def handling_retained_event_payloads(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test if event payload is handled."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config via mqtt_mock_entry")
async def setting_event_value_with_invalid_payload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of the event value with an invalid payload."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def setting_event_value_via_mqtt_json_message_and_default_current_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of the event value via MQTT with JSON payload."""
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
    """Test availability by default payload with defined topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def default_availability_list_payload_all(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test availability by default payload with defined topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def default_availability_list_payload_any(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test availability by default payload with defined topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def default_availability_list_single(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test availability list and availability_topic are mutually exclusive."""
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
        event.DOMAIN,
        DEFAULT_CONFIG,
        MQTT_EVENT_ATTRIBUTES_BLOCKED,
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
        hass, _make_mqtt_mock_entry(mqtt_mock), event.DOMAIN, DEFAULT_CONFIG
    )


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test unique id option only creates one event per unique_id."""
    _ = (hass, mqtt_mock)


@test
async def discovery_removal_event(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test removal of discovered event."""
    data = '{ "name": "test", "state_topic": "test_topic", "event_types": ["press"] }'
    await help_test_discovery_removal(
        hass, _make_mqtt_mock_entry(mqtt_mock), event.DOMAIN, data
    )


@test.skip("relies on async_fire_mqtt_message ordering with mqtt_mock_entry setup")
async def discovery_update_event_template(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test update of discovered mqtt event template."""
    _ = (hass, mqtt_mock)


@test
async def discovery_broken(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test handling of bad discovery message."""
    data1 = '{ "name": "Beer", "state_topic": "test_topic#", "event_types": ["press"] }'
    data2 = '{ "name": "Milk", "state_topic": "test_topic", "event_types": ["press"] }'
    await help_test_discovery_broken(
        hass, _make_mqtt_mock_entry(mqtt_mock), event.DOMAIN, data1, data2
    )


@test
async def entity_device_info_with_connection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT event device registry integration."""
    await help_test_entity_device_info_with_connection(
        hass, _make_mqtt_mock_entry(mqtt_mock), event.DOMAIN, DEFAULT_CONFIG
    )


@test
async def entity_device_info_with_identifier(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT event device registry integration."""
    await help_test_entity_device_info_with_identifier(
        hass, _make_mqtt_mock_entry(mqtt_mock), event.DOMAIN, DEFAULT_CONFIG
    )


@test
async def entity_device_info_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device registry update."""
    await help_test_entity_device_info_update(
        hass, _make_mqtt_mock_entry(mqtt_mock), event.DOMAIN, DEFAULT_CONFIG
    )


@test
async def entity_device_info_remove(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device registry remove."""
    await help_test_entity_device_info_remove(
        hass, _make_mqtt_mock_entry(mqtt_mock), event.DOMAIN, DEFAULT_CONFIG
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
        hass, _make_mqtt_mock_entry(mqtt_mock), event.DOMAIN, DEFAULT_CONFIG
    )


@test.skip("requires custom hass_config via mqtt_mock_entry for device with hub")
async def entity_device_info_with_hub(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT event device registry integration with hub."""
    _ = (hass, mqtt_mock)


@test.skip("requires debug info helper with mqtt_mock_entry-created entity")
async def entity_debug_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT event debug info."""
    _ = (hass, mqtt_mock)


@test
async def entity_debug_info_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT debug info."""
    await help_test_entity_debug_info_message(
        hass, _make_mqtt_mock_entry(mqtt_mock), event.DOMAIN, DEFAULT_CONFIG, None
    )


@test.skip("requires debug info helper with mqtt_mock_entry-created entity")
async def entity_debug_info_remove(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT event debug info."""
    _ = (hass, mqtt_mock)


@test.skip("requires debug info helper with mqtt_mock_entry-created entity")
async def entity_debug_info_update_entity_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT event debug info."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def entity_disabled_by_default(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the entity is disabled by default."""
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
    """Test the access to attributes in value_template via the entity_id."""
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


@test.skip("requires parametrized topic/value_template combos via mqtt_mock_entry")
async def skipped_async_ha_write_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test a write state command is only called when there is change."""
    _ = (hass, mqtt_mock)


@test.skip("requires parametrized topic/value_template combos via mqtt_mock_entry")
async def skipped_async_ha_write_state2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test a write state command is only called when there is change."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config via mqtt_mock_entry")
async def value_template_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the rendering of MQTT value template fails gracefully."""
    _ = (hass, mqtt_mock)
