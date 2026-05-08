"""Tryke skip-stubs for test_select.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def all_entities() -> None:
    """Stub for test_all_entities."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def set_select() -> None:
    """Stub for test_set_select."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def select_error() -> None:
    """Stub for test_select_error."""
