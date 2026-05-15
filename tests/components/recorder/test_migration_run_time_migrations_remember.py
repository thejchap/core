"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def data_migrator_logic() -> None:
    """Stub for test_data_migrator_logic (port deferred)."""

@test.skip("pending tryke port")
async def migration_changes_prevent_trying_to_migrate_again() -> None:
    """Stub for test_migration_changes_prevent_trying_to_migrate_again (port deferred)."""
