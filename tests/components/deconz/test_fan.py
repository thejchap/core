"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def fans() -> None:
    """Stub for test_fans (port deferred)."""
