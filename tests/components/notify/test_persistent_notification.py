"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def async_send_message() -> None:
    """Stub for test_async_send_message (port deferred)."""

@test.skip("pending tryke port")
async def async_supports_notification_id() -> None:
    """Stub for test_async_supports_notification_id (port deferred)."""
