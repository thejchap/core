"""Tryke skip-stubs for test_sensor.py - sibling port deferred (66 LOC, 2 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (66 LOC, 2 parametrize)")
async def outdoor_sensor() -> None:
    """Stub for test_outdoor_sensor."""

@test.skip("sibling port deferred (66 LOC, 2 parametrize)")
async def indoor_sensor() -> None:
    """Stub for test_indoor_sensor."""
