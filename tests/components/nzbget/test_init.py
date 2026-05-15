"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""

@test.skip("pending tryke port")
async def async_setup_raises_entry_not_ready() -> None:
    """Stub for test_async_setup_raises_entry_not_ready (port deferred)."""
