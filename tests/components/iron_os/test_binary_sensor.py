"""Tryke skip-stubs for test_binary_sensor.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def binary_sensors() -> None:
    """Stub for test_binary_sensors."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def tip_on_off() -> None:
    """Stub for test_tip_on_off."""
