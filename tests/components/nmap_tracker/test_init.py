"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def migrate_entry() -> None:
    """Stub for test_migrate_entry (port deferred)."""

@test.skip("pending tryke port")
async def migrate_entry_fails_on_downgrade() -> None:
    """Stub for test_migrate_entry_fails_on_downgrade (port deferred)."""
