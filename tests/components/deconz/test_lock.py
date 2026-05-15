"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def lock_from_light() -> None:
    """Stub for test_lock_from_light (port deferred)."""

@test.skip("pending tryke port")
async def lock_from_sensor() -> None:
    """Stub for test_lock_from_sensor (port deferred)."""
