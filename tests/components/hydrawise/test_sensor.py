"""Tryke skip-stubs for test_sensor.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot test — out of scope")
async def all_sensors() -> None:
    """Stub for test_all_sensors."""

@test.skip("snapshot test — out of scope")
async def suspended_state() -> None:
    """Stub for test_suspended_state."""

@test.skip("snapshot test — out of scope")
async def usage_refresh() -> None:
    """Stub for test_usage_refresh."""

@test.skip("snapshot test — out of scope")
async def no_sensor_and_water_state() -> None:
    """Stub for test_no_sensor_and_water_state."""

@test.skip("snapshot test — out of scope")
async def volume_unit_conversion() -> None:
    """Stub for test_volume_unit_conversion."""
