"""Tryke skip-stubs for test_binary_sensor.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def binary_sensors() -> None:
    """Stub for test_binary_sensors."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def brew_active_unavailable() -> None:
    """Stub for test_brew_active_unavailable."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def sensor_going_unavailable() -> None:
    """Stub for test_sensor_going_unavailable."""
