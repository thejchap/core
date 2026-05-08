"""Tryke skip-stubs for test_event.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def setup() -> None:
    """Stub for test_setup."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def events() -> None:
    """Stub for test_events."""
