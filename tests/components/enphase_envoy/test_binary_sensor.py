"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def binary_sensor() -> None:
    """Stub for test_binary_sensor (port deferred)."""

@test.skip("snapshot test - port deferred")
async def no_binary_sensor() -> None:
    """Stub for test_no_binary_sensor (port deferred)."""

@test.skip("snapshot test - port deferred")
async def binary_sensor_data() -> None:
    """Stub for test_binary_sensor_data (port deferred)."""
