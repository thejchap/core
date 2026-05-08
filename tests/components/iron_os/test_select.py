"""Tryke skip-stubs for test_select.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def state() -> None:
    """Stub for test_state."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def select_option() -> None:
    """Stub for test_select_option."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def select_option_exception() -> None:
    """Stub for test_select_option_exception."""
