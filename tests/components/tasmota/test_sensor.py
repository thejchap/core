"""Tryke skip-stubs for tasmota/test_sensor.py."""

from tryke import test


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
async def attributes() -> None:
    """Stub for test_attributes."""

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

