"""Tryke skip-stubs for test_select.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def select_services() -> None:
    """Stub for test_select_services."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def select_option_service_error() -> None:
    """Stub for test_select_option_service_error."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def select_snapshot() -> None:
    """Stub for test_select_snapshot."""
