"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def entry_diagnostics() -> None:
    """Stub for test_entry_diagnostics (port deferred)."""

@test.skip("snapshot test - port deferred")
async def device_diagnostics() -> None:
    """Stub for test_device_diagnostics (port deferred)."""
