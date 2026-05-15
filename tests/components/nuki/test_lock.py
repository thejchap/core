"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def locks() -> None:
    """Stub for test_locks (port deferred)."""
