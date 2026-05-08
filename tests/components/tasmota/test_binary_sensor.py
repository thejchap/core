"""Tryke skip-stubs for tasmota/test_binary_sensor.py."""

from tryke import test


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def controlling_state_via_mqtt() -> None:
    """Stub for test_controlling_state_via_mqtt."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def controlling_state_via_mqtt_switchname() -> None:
    """Stub for test_controlling_state_via_mqtt_switchname."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def pushon_controlling_state_via_mqtt() -> None:
    """Stub for test_pushon_controlling_state_via_mqtt."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def friendly_names() -> None:
    """Stub for test_friendly_names."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def off_delay() -> None:
    """Stub for test_off_delay."""

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
async def discovery_removal_binary_sensor() -> None:
    """Stub for test_discovery_removal_binary_sensor."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def discovery_update_unchanged_binary_sensor() -> None:
    """Stub for test_discovery_update_unchanged_binary_sensor."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def discovery_device_remove() -> None:
    """Stub for test_discovery_device_remove."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def entity_id_update_subscriptions() -> None:
    """Stub for test_entity_id_update_subscriptions."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def entity_id_update_discovery_update() -> None:
    """Stub for test_entity_id_update_discovery_update."""

