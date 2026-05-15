"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def send_message() -> None:
    """Stub for test_send_message (port deferred)."""

@test.skip("pending tryke port")
async def unsendable_message() -> None:
    """Stub for test_unsendable_message (port deferred)."""
