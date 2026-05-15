"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def import() -> None:
    """Stub for test_import (port deferred)."""

@test.skip("pending tryke port")
async def import_changed() -> None:
    """Stub for test_import_changed (port deferred)."""

@test.skip("pending tryke port")
async def request_sync_service() -> None:
    """Stub for test_request_sync_service (port deferred)."""
