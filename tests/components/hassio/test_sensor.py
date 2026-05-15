"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def sensor() -> None:
    """Stub for test_sensor (port deferred)."""

@test.skip("pending tryke port")
async def stats_addon_sensor() -> None:
    """Stub for test_stats_addon_sensor (port deferred)."""
