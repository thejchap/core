"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def full_flow() -> None:
    """Stub for test_full_flow (port deferred)."""

@test.skip("pending tryke port")
async def not_found() -> None:
    """Stub for test_not_found (port deferred)."""
