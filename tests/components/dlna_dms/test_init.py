"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def resource_lifecycle() -> None:
    """Stub for test_resource_lifecycle (port deferred)."""

@test.skip("pending tryke port")
async def migrate_entry() -> None:
    """Stub for test_migrate_entry (port deferred)."""

@test.skip("pending tryke port")
async def migrate_entry_collision() -> None:
    """Stub for test_migrate_entry_collision (port deferred)."""
