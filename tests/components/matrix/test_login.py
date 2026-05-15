"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def login() -> None:
    """Stub for test_login (port deferred)."""

@test.skip("pending tryke port")
async def get_auth_tokens() -> None:
    """Stub for test_get_auth_tokens (port deferred)."""
