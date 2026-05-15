"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def send_simple_message() -> None:
    """Stub for test_send_simple_message (port deferred)."""

@test.skip("pending tryke port")
async def send_multiple_message() -> None:
    """Stub for test_send_multiple_message (port deferred)."""

@test.skip("pending tryke port")
async def send_message_attachment() -> None:
    """Stub for test_send_message_attachment (port deferred)."""

@test.skip("pending tryke port")
async def send_targetless_message() -> None:
    """Stub for test_send_targetless_message (port deferred)."""

@test.skip("pending tryke port")
async def send_message_with_400() -> None:
    """Stub for test_send_message_with_400 (port deferred)."""
