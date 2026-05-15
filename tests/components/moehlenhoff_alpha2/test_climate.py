"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def climate() -> None:
    """Stub for test_climate (port deferred)."""
