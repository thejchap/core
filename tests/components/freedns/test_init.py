"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""

@test.skip("pending tryke port")
async def setup_fails_if_wrong_token() -> None:
    """Stub for test_setup_fails_if_wrong_token (port deferred)."""
