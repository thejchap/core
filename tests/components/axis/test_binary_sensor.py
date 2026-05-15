"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def binary_sensors() -> None:
    """Stub for test_binary_sensors (port deferred)."""

@test.skip("snapshot test - port deferred")
async def unsupported_events() -> None:
    """Stub for test_unsupported_events (port deferred)."""
