"""Tryke skip-stubs for ntfy test_notify (port deferred)."""
from tryke import test

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def send_message_reauth_flow() -> None:
    """Stub for test_send_message_reauth_flow (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def notify_platform() -> None:
    """Stub for test_notify_platform (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def send_message() -> None:
    """Stub for test_send_message (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def send_message_exception() -> None:
    """Stub for test_send_message_exception (port deferred)."""


