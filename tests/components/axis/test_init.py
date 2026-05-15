"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_entry() -> None:
    """Stub for test_setup_entry (port deferred)."""

@test.skip("pending tryke port")
async def setup_entry_fails() -> None:
    """Stub for test_setup_entry_fails (port deferred)."""

@test.skip("pending tryke port")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""

@test.skip("pending tryke port")
async def migrate_entry() -> None:
    """Stub for test_migrate_entry (port deferred)."""
