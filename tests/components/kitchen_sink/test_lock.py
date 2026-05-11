"""Tryke skip-stubs for test_lock.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot test — out of scope")
async def states() -> None:
    """Stub for test_states."""

@test.skip("snapshot test — out of scope")
async def locking() -> None:
    """Stub for test_locking."""

@test.skip("snapshot test — out of scope")
async def unlocking() -> None:
    """Stub for test_unlocking."""

@test.skip("snapshot test — out of scope")
async def opening_mocked() -> None:
    """Stub for test_opening_mocked."""

@test.skip("snapshot test — out of scope")
async def opening() -> None:
    """Stub for test_opening."""
