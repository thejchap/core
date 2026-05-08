"""Tryke skip-stubs for test_update.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def update() -> None:
    """Stub for test_update."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def update_min_version() -> None:
    """Stub for test_update_min_version."""
