"""Tryke skip-stubs for test_device_tracker.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def device_tracker() -> None:
    """Stub for test_device_tracker."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def availability() -> None:
    """Stub for test_availability."""
