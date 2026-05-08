"""Tryke skip-stubs for tasmota/test_device_trigger.py."""

from tryke import test


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def get_triggers_btn() -> None:
    """Stub for test_get_triggers_btn."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def get_triggers_swc() -> None:
    """Stub for test_get_triggers_swc."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def get_unknown_triggers() -> None:
    """Stub for test_get_unknown_triggers."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def get_non_existing_triggers() -> None:
    """Stub for test_get_non_existing_triggers."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def discover_bad_triggers() -> None:
    """Stub for test_discover_bad_triggers."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def update_remove_triggers() -> None:
    """Stub for test_update_remove_triggers."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def if_fires_on_mqtt_message_btn() -> None:
    """Stub for test_if_fires_on_mqtt_message_btn."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def if_fires_on_mqtt_message_swc() -> None:
    """Stub for test_if_fires_on_mqtt_message_swc."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def if_fires_on_mqtt_message_late_discover() -> None:
    """Stub for test_if_fires_on_mqtt_message_late_discover."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def if_fires_on_mqtt_message_after_update() -> None:
    """Stub for test_if_fires_on_mqtt_message_after_update."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def no_resubscribe_same_topic() -> None:
    """Stub for test_no_resubscribe_same_topic."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def not_fires_on_mqtt_message_after_remove_by_mqtt() -> None:
    """Stub for test_not_fires_on_mqtt_message_after_remove_by_mqtt."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def not_fires_on_mqtt_message_after_remove_from_registry() -> None:
    """Stub for test_not_fires_on_mqtt_message_after_remove_from_registry."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def attach_remove() -> None:
    """Stub for test_attach_remove."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def attach_remove_late() -> None:
    """Stub for test_attach_remove_late."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def attach_remove_late2() -> None:
    """Stub for test_attach_remove_late2."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def attach_remove_unknown1() -> None:
    """Stub for test_attach_remove_unknown1."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def attach_unknown_remove_device_from_registry() -> None:
    """Stub for test_attach_unknown_remove_device_from_registry."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def attach_remove_config_entry() -> None:
    """Stub for test_attach_remove_config_entry."""

