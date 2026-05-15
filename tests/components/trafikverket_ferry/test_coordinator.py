"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def coordinator() -> None:
    """Stub for test_coordinator (port deferred)."""

@test.skip("pending tryke port")
async def coordinator_next_departuredate() -> None:
    """Stub for test_coordinator_next_departuredate (port deferred)."""
