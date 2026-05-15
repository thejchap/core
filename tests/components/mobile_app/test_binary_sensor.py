"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def sensor() -> None:
    """Stub for test_sensor (port deferred)."""

@test.skip("pending tryke port")
async def sensor_must_register() -> None:
    """Stub for test_sensor_must_register (port deferred)."""

@test.skip("pending tryke port")
async def sensor_id_no_dupes() -> None:
    """Stub for test_sensor_id_no_dupes (port deferred)."""

@test.skip("pending tryke port")
async def register_sensor_no_state() -> None:
    """Stub for test_register_sensor_no_state (port deferred)."""

@test.skip("pending tryke port")
async def update_sensor_no_state() -> None:
    """Stub for test_update_sensor_no_state (port deferred)."""

@test.skip("pending tryke port")
async def dispatcher_cleanup_on_unload() -> None:
    """Stub for test_dispatcher_cleanup_on_unload (port deferred)."""
