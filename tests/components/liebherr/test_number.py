"""Tryke skip-stubs for test_number.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def numbers() -> None:
    """Stub for test_numbers."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def single_zone_number() -> None:
    """Stub for test_single_zone_number."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def set_temperature() -> None:
    """Stub for test_set_temperature."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def set_temperature_failure() -> None:
    """Stub for test_set_temperature_failure."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def number_when_control_missing() -> None:
    """Stub for test_number_when_control_missing."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def number_with_none_min_max() -> None:
    """Stub for test_number_with_none_min_max."""
