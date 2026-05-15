"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires mqtt_mock (not in tryke shim)")
async def no_mqtt() -> None:
    """Stub for test_no_mqtt (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def room_update() -> None:
    """Stub for test_room_update (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def unique_id_is_set() -> None:
    """Stub for test_unique_id_is_set (port deferred)."""
