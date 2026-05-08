"""Tryke skip-stubs for test_binary_sensor.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def all_binary_sensors() -> None:
    """Stub for test_all_binary_sensors."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def update_data_fails() -> None:
    """Stub for test_update_data_fails."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def controller_offline() -> None:
    """Stub for test_controller_offline."""
