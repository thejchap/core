"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def signal_strength() -> None:
    """Stub for test_signal_strength (port deferred)."""

@test.skip("pending tryke port")
async def power_monitoring() -> None:
    """Stub for test_power_monitoring (port deferred)."""
