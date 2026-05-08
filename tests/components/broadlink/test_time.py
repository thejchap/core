"""Tryke skip stub for test_time.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def time() -> None:
    """Stub for test_time."""

