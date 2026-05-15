"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def sync_turn_on() -> None:
    """Stub for test_sync_turn_on (port deferred)."""

@test.skip("pending tryke port")
async def sync_turn_off() -> None:
    """Stub for test_sync_turn_off (port deferred)."""

@test.skip("pending tryke port")
async def humidity_validation() -> None:
    """Stub for test_humidity_validation (port deferred)."""
