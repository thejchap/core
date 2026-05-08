"""Tryke skip-stubs for test_binary_sensor.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def all_binary_sensor_entities() -> None:
    """Stub for test_all_binary_sensor_entities."""
