"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def steam_active() -> None:
    """Stub for test_steam_active (port deferred)."""

@test.skip("pending tryke port")
async def steam_inactive() -> None:
    """Stub for test_steam_inactive (port deferred)."""
