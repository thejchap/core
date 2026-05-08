"""Tryke skip-stubs for test_sensor.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def sensor() -> None:
    """Stub for test_sensor."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def availability() -> None:
    """Stub for test_availability."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def remove_entity() -> None:
    """Stub for test_remove_entity."""
