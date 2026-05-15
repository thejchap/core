"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def device_entry() -> None:
    """Stub for test_device_entry (port deferred)."""

@test.skip("snapshot test - port deferred")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""
