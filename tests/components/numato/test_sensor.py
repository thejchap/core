"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def failing_setups_no_entities() -> None:
    """Stub for test_failing_setups_no_entities (port deferred)."""

@test.skip("pending tryke port")
async def failing_sensor_update() -> None:
    """Stub for test_failing_sensor_update (port deferred)."""

@test.skip("pending tryke port")
async def sensor_setup_without_discovery_info() -> None:
    """Stub for test_sensor_setup_without_discovery_info (port deferred)."""
