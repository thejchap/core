"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""

@test.skip("pending tryke port")
async def windows() -> None:
    """Stub for test_windows (port deferred)."""

@test.skip("pending tryke port")
async def update_failed() -> None:
    """Stub for test_update_failed (port deferred)."""
