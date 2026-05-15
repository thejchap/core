"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""

@test.skip("snapshot test - port deferred")
async def sensor_updates() -> None:
    """Stub for test_sensor_updates (port deferred)."""
