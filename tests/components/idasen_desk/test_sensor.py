"""Tryke skip-stubs for test_sensor.py - sibling port deferred (69 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (69 LOC, 0 parametrize)")
async def height_sensor() -> None:
    """Stub for test_height_sensor."""

@test.skip("sibling port deferred (69 LOC, 0 parametrize)")
async def sensor_available() -> None:
    """Stub for test_sensor_available."""
