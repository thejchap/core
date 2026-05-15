"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""

@test.skip("pending tryke port")
async def sensor_no_unique_id() -> None:
    """Stub for test_sensor_no_unique_id (port deferred)."""
