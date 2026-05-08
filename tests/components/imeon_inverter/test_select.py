"""Tryke skip-stubs for test_select.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def selects() -> None:
    """Stub for test_selects."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def select_mode() -> None:
    """Stub for test_select_mode."""
