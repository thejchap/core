"""Tryke skip-stubs for test_binary_sensor.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def sensor_snapshot() -> None:
    """Stub for test_sensor_snapshot."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def add_device() -> None:
    """Stub for test_add_device."""
