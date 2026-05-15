"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def sensor_state() -> None:
    """Stub for test_sensor_state (port deferred)."""

@test.skip("pending tryke port")
async def sensor_error() -> None:
    """Stub for test_sensor_error (port deferred)."""

@test.skip("pending tryke port")
async def sensor_empty_response() -> None:
    """Stub for test_sensor_empty_response (port deferred)."""

@test.skip("pending tryke port")
async def sensor_attributes() -> None:
    """Stub for test_sensor_attributes (port deferred)."""
