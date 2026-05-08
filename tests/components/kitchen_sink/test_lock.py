"""Tryke skip-stubs for test_lock.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def states() -> None:
    """Stub for test_states."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def locking() -> None:
    """Stub for test_locking."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def unlocking() -> None:
    """Stub for test_unlocking."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def opening_mocked() -> None:
    """Stub for test_opening_mocked."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def opening() -> None:
    """Stub for test_opening."""
