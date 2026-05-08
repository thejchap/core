"""Tryke skip-stubs for test_binary_sensor.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def binary_sensor_attributes_state_update() -> None:
    """Stub for test_binary_sensor_attributes_state_update."""
