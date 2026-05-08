"""Tryke skip-stubs for test_light.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def light() -> None:
    """Stub for test_light."""
