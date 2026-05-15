"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def update() -> None:
    """Stub for test_update (port deferred)."""

@test.skip("pending tryke port")
async def update_no_versions() -> None:
    """Stub for test_update_no_versions (port deferred)."""

@test.skip("pending tryke port")
async def update_no_updates() -> None:
    """Stub for test_update_no_updates (port deferred)."""
