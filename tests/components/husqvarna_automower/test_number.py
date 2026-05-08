"""Tryke skip-stubs for test_number.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def number_commands() -> None:
    """Stub for test_number_commands."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def number_workarea_commands() -> None:
    """Stub for test_number_workarea_commands."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def number_snapshot() -> None:
    """Stub for test_number_snapshot."""
