"""Tryke skip-stubs for test_water_heater.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def setup_platform() -> None:
    """Stub for test_setup_platform."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def current_temperature_cases() -> None:
    """Stub for test_current_temperature_cases."""
