"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""

@test.skip("pending tryke port")
async def sensor_dark() -> None:
    """Stub for test_sensor_dark (port deferred)."""

@test.skip("pending tryke port")
async def sensor_unknown_error() -> None:
    """Stub for test_sensor_unknown_error (port deferred)."""
