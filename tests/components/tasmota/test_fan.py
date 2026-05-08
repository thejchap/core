"""Tryke skip-stubs for tasmota/test_fan.py."""

from tryke import test


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def controlling_state_via_mqtt() -> None:
    """Stub for test_controlling_state_via_mqtt."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def sending_mqtt_commands() -> None:
    """Stub for test_sending_mqtt_commands."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def invalid_fan_speed_percentage() -> None:
    """Stub for test_invalid_fan_speed_percentage."""

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
async def discovery_removal_fan() -> None:
    """Stub for test_discovery_removal_fan."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def discovery_update_unchanged_fan() -> None:
    """Stub for test_discovery_update_unchanged_fan."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def discovery_device_remove() -> None:
    """Stub for test_discovery_device_remove."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def entity_id_update_subscriptions() -> None:
    """Stub for test_entity_id_update_subscriptions."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def entity_id_update_discovery_update() -> None:
    """Stub for test_entity_id_update_discovery_update."""

