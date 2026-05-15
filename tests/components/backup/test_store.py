"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def store_migration() -> None:
    """Stub for test_store_migration (port deferred)."""
