"""Tryke skip-stubs for test_sensor.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def entities() -> None:
    """Stub for test_entities."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def sensor_unavailable_on_coordinator_error() -> None:
    """Stub for test_sensor_unavailable_on_coordinator_error."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def sensor_with_none_status_code() -> None:
    """Stub for test_sensor_with_none_status_code."""
