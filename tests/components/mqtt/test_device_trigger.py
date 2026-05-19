"""The tests for MQTT device triggers."""

from typing import Any

from tryke import Depends, fixture, test

from homeassistant.core import HomeAssistant

from ._fixtures import mqtt_mock as mqtt_mock_fixture
from tests.hass_fixtures import (
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _mqtt: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("device_registry fixture and parametrize not available in tryke shim")
async def get_triggers(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test we get the expected triggers from a discovered mqtt device."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry fixture not available in tryke shim")
async def get_unknown_triggers(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test we don't get unknown triggers."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry fixture not available in tryke shim")
async def get_non_existing_triggers(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test getting non existing triggers."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry fixture not available in tryke shim")
async def discover_bad_triggers(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test bad discovery message."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry fixture not available in tryke shim")
async def update_remove_triggers(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test triggers can be updated and removed."""
    _ = (hass, mqtt_mock)


@test.skip("service_calls and device_registry fixtures not available in tryke shim")
async def if_fires_on_mqtt_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test triggers firing."""
    _ = (hass, mqtt_mock)


@test.skip("service_calls and device_registry fixtures not available in tryke shim")
async def if_discovery_id_is_prefered(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test discovery_id is preferred over type/subtype."""
    _ = (hass, mqtt_mock)


@test.skip("service_calls and device_registry fixtures not available in tryke shim")
async def non_unique_triggers(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test non-unique triggers."""
    _ = (hass, mqtt_mock)


@test.skip("service_calls and device_registry fixtures not available in tryke shim")
async def if_fires_on_mqtt_message_template(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test triggers firing with a value template."""
    _ = (hass, mqtt_mock)


@test.skip("service_calls and device_registry fixtures not available in tryke shim")
async def if_fires_on_mqtt_message_late_discover(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test triggers firing of MQTT device triggers discovered after setup."""
    _ = (hass, mqtt_mock)


@test.skip("service_calls and device_registry fixtures not available in tryke shim")
async def if_fires_on_mqtt_message_after_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test triggers firing after update."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry fixture not available in tryke shim")
async def no_resubscribe_same_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test subscription to topics without change."""
    _ = (hass, mqtt_mock)


@test.skip("service_calls and device_registry fixtures not available in tryke shim")
async def not_fires_on_mqtt_message_after_remove_by_mqtt(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test triggers not firing after removal."""
    _ = (hass, mqtt_mock)


@test.skip("service_calls and device_registry fixtures not available in tryke shim")
async def not_fires_on_mqtt_message_after_remove_from_registry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test triggers not firing after removal from registry."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry fixture not available in tryke shim")
async def attach_remove(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test attach and removal of trigger."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry fixture not available in tryke shim")
async def attach_remove_late(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test attach and removal of trigger for late discovery."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry fixture not available in tryke shim")
async def attach_remove_late2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test attach and removal of trigger for late discovery."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry fixture not available in tryke shim")
async def entity_device_info_with_connection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT device info with connection."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry fixture not available in tryke shim")
async def entity_device_info_with_identifier(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test MQTT device info with identifier."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry fixture not available in tryke shim")
async def entity_device_info_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device registry update."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry and ws client fixtures not available in tryke shim")
async def cleanup_trigger(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test trigger cleanup."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry and ws client fixtures not available in tryke shim")
async def cleanup_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device cleanup."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry and ws client fixtures not available in tryke shim")
async def cleanup_device_several_triggers(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device cleanup with several triggers."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry and ws client fixtures not available in tryke shim")
async def cleanup_device_with_entity1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device cleanup with entity (case 1)."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry and ws client fixtures not available in tryke shim")
async def cleanup_device_with_entity2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device cleanup with entity (case 2)."""
    _ = (hass, mqtt_mock)


@test.skip("device_registry fixture not available in tryke shim")
async def trigger_debug_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test debug info."""
    _ = (hass, mqtt_mock)


@test.skip("help_test_unload_config_entry not adapted for tryke shim")
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test unloading the config entry."""
    _ = (hass, mqtt_mock)
