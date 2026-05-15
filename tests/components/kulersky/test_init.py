"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def migrate_entry() -> None:
    """Stub for test_migrate_entry (port deferred)."""

@test.skip("pending tryke port")
async def migrate_entry_no_devices_found() -> None:
    """Stub for test_migrate_entry_no_devices_found (port deferred)."""
