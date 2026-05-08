"""Tryke skip-stubs for test_sensor.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def sensors() -> None:
    """Stub for test_sensors."""
