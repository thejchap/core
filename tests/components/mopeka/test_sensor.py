"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def sensors_unusable_signal() -> None:
    """Stub for test_sensors_unusable_signal (port deferred)."""

@test.skip("pending tryke port")
async def sensors_poor_signal() -> None:
    """Stub for test_sensors_poor_signal (port deferred)."""

@test.skip("pending tryke port")
async def sensors_good_signal() -> None:
    """Stub for test_sensors_good_signal (port deferred)."""
