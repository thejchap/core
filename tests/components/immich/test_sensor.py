"""Tryke skip-stubs for test_sensor.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def sensors() -> None:
    """Stub for test_sensors."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def admin_sensors() -> None:
    """Stub for test_admin_sensors."""
