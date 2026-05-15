"""Tryke skip stub for CityBikes sensor tests."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def sensor_state() -> None:
    """Stub for test_sensor_state (port deferred)."""
