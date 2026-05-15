"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def sensor() -> None:
    """Stub for test_sensor (port deferred)."""

@test.skip("snapshot test - port deferred")
async def faulting_points() -> None:
    """Stub for test_faulting_points (port deferred)."""

@test.skip("snapshot test - port deferred")
async def alarm_faults() -> None:
    """Stub for test_alarm_faults (port deferred)."""
