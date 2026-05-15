"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def invalid_credentials() -> None:
    """Stub for test_invalid_credentials (port deferred)."""

@test.skip("pending tryke port")
async def valid_credentials() -> None:
    """Stub for test_valid_credentials (port deferred)."""
