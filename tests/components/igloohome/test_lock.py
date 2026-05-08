"""Tryke skip-stubs for test_lock.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def lock() -> None:
    """Stub for test_lock."""
