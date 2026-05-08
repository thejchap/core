"""Tryke skip-stubs for test_valve.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def all_valves() -> None:
    """Stub for test_all_valves."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def services() -> None:
    """Stub for test_services."""
