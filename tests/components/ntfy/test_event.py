"""Tryke skip-stubs for ntfy test_event (port deferred)."""
from tryke import test

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def event_topic_protected() -> None:
    """Stub for test_event_topic_protected (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def event_platform() -> None:
    """Stub for test_event_platform (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def event() -> None:
    """Stub for test_event (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def event_exceptions() -> None:
    """Stub for test_event_exceptions (port deferred)."""


