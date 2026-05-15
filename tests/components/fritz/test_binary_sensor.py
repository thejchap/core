"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def binary_sensor_setup() -> None:
    """Stub for test_binary_sensor_setup (port deferred)."""

@test.skip("snapshot test - port deferred")
async def binary_sensor_missing_state() -> None:
    """Stub for test_binary_sensor_missing_state (port deferred)."""
