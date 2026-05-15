"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def update_success() -> None:
    """Stub for test_update_success (port deferred)."""

@test.skip("pending tryke port")
async def update_failure() -> None:
    """Stub for test_update_failure (port deferred)."""
