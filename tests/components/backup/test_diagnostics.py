"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def diagnostics() -> None:
    """Stub for test_diagnostics (port deferred)."""
