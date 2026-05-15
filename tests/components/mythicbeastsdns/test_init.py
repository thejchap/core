"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def update() -> None:
    """Stub for test_update (port deferred)."""

@test.skip("pending tryke port")
async def update_fails_if_wrong_token() -> None:
    """Stub for test_update_fails_if_wrong_token (port deferred)."""

@test.skip("pending tryke port")
async def update_fails_if_invalid_host() -> None:
    """Stub for test_update_fails_if_invalid_host (port deferred)."""
