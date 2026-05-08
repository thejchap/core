"""Tryke skip stub for test_lock.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def locking() -> None:
    """Stub for test_locking."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unlocking() -> None:
    """Stub for test_unlocking."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def opening() -> None:
    """Stub for test_opening."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def jammed_when_locking() -> None:
    """Stub for test_jammed_when_locking."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def opening_mocked() -> None:
    """Stub for test_opening_mocked."""

