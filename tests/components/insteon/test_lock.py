"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def lock_lock() -> None:
    """Stub for test_lock_lock (port deferred)."""

@test.skip("pending tryke port")
async def lock_unlock() -> None:
    """Stub for test_lock_unlock (port deferred)."""
