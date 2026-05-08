"""Tryke skip-stubs for nest test_event (port deferred)."""
from tryke import test

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def event_threads() -> None:
    """Stub for test_event_threads (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def receive_events() -> None:
    """Stub for test_receive_events (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def ignore_unrelated_event() -> None:
    """Stub for test_ignore_unrelated_event (port deferred)."""


