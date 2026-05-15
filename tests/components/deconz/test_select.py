"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def select() -> None:
    """Stub for test_select (port deferred)."""
