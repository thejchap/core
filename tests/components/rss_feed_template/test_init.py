"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def get_nonexistant_feed() -> None:
    """Stub for test_get_nonexistant_feed (port deferred)."""

@test.skip("pending tryke port")
async def get_rss_feed() -> None:
    """Stub for test_get_rss_feed (port deferred)."""
