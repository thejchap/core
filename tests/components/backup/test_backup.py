"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def load_backups() -> None:
    """Stub for test_load_backups (port deferred)."""

@test.skip("snapshot test - port deferred")
async def upload() -> None:
    """Stub for test_upload (port deferred)."""

@test.skip("snapshot test - port deferred")
async def delete_backup() -> None:
    """Stub for test_delete_backup (port deferred)."""
