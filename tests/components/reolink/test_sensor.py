"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""

@test.skip("pending tryke port")
async def hdd_sensors() -> None:
    """Stub for test_hdd_sensors (port deferred)."""
