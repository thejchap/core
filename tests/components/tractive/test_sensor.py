"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def sensor() -> None:
    """Stub for test_sensor (port deferred)."""
