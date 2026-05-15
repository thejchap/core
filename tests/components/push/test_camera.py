"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def bad_posting() -> None:
    """Stub for test_bad_posting (port deferred)."""

@test.skip("pending tryke port")
async def posting_url() -> None:
    """Stub for test_posting_url (port deferred)."""
