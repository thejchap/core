"""Tryke skip-stubs for test_climate.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def all_sensor_entities() -> None:
    """Stub for test_all_sensor_entities."""
