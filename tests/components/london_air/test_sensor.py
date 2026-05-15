"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def valid_state() -> None:
    """Stub for test_valid_state (port deferred)."""

@test.skip("pending tryke port")
async def api_failure() -> None:
    """Stub for test_api_failure (port deferred)."""
