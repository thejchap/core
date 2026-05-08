"""Tryke skip-stubs for ntfy test_sensor (port deferred)."""
from tryke import test

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""


