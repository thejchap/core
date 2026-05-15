"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""

@test.skip("pending tryke port")
async def setup_error() -> None:
    """Stub for test_setup_error (port deferred)."""

@test.skip("pending tryke port")
async def setup_error_no_station() -> None:
    """Stub for test_setup_error_no_station (port deferred)."""

@test.skip("pending tryke port")
async def sensor_values() -> None:
    """Stub for test_sensor_values (port deferred)."""
