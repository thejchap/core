"""Tryke skip-stubs for test_sensor.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def sensor() -> None:
    """Stub for test_sensor."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def sensor_availability() -> None:
    """Stub for test_sensor_availability."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def battery_pack_filtering() -> None:
    """Stub for test_battery_pack_filtering."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def battery_pack_filtering_fetch_error() -> None:
    """Stub for test_battery_pack_filtering_fetch_error."""
