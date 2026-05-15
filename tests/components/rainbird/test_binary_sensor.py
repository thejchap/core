"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def rainsensor() -> None:
    """Stub for test_rainsensor (port deferred)."""

@test.skip("pending tryke port")
async def no_unique_id() -> None:
    """Stub for test_no_unique_id (port deferred)."""
