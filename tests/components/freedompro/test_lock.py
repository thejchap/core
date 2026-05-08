"""Tryke skip stub for test_lock.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def lock_get_state() -> None:
    """Stub for test_lock_get_state."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def lock_set_unlock() -> None:
    """Stub for test_lock_set_unlock."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def lock_set_lock() -> None:
    """Stub for test_lock_set_lock."""

