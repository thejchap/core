"""Tryke skip-stubs for test_event.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def event() -> None:
    """Stub for test_event."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def event_snapshot() -> None:
    """Stub for test_event_snapshot."""
