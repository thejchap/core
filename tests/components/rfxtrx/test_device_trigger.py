"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def get_triggers() -> None:
    """Stub for test_get_triggers (port deferred)."""

@test.skip("pending tryke port")
async def firing_event() -> None:
    """Stub for test_firing_event (port deferred)."""

@test.skip("pending tryke port")
async def invalid_trigger() -> None:
    """Stub for test_invalid_trigger (port deferred)."""
