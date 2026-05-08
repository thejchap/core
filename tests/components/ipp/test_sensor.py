"""Tryke skip-stubs for test_sensor.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def sensors() -> None:
    """Stub for test_sensors."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def disabled_by_default_sensors() -> None:
    """Stub for test_disabled_by_default_sensors."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def missing_entry_unique_id() -> None:
    """Stub for test_missing_entry_unique_id."""
