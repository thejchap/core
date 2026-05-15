"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def event_entity() -> None:
    """Stub for test_event_entity (port deferred)."""

@test.skip("snapshot test - port deferred")
async def event_entity_backup_completed() -> None:
    """Stub for test_event_entity_backup_completed (port deferred)."""

@test.skip("snapshot test - port deferred")
async def event_entity_backup_failed() -> None:
    """Stub for test_event_entity_backup_failed (port deferred)."""
