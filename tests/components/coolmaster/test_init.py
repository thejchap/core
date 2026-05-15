"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def load_entry() -> None:
    """Stub for test_load_entry (port deferred)."""

@test.skip("pending tryke port")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""

@test.skip("pending tryke port")
async def registry_cleanup() -> None:
    """Stub for test_registry_cleanup (port deferred)."""
