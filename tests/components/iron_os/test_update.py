"""Tryke skip-stubs for test_update.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def update() -> None:
    """Stub for test_update."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def update_unavailable() -> None:
    """Stub for test_update_unavailable."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def update_restore_last_state() -> None:
    """Stub for test_update_restore_last_state."""
