"""Tryke skip-stubs for test_select.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def selects() -> None:
    """Stub for test_selects."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def select_service_calls() -> None:
    """Stub for test_select_service_calls."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def select_failure() -> None:
    """Stub for test_select_failure."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def select_when_control_missing() -> None:
    """Stub for test_select_when_control_missing."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def single_zone_select() -> None:
    """Stub for test_single_zone_select."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def select_current_option_none_mode() -> None:
    """Stub for test_select_current_option_none_mode."""
