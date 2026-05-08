"""Tryke skip stub for test_remote.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def methods() -> None:
    """Stub for test_methods."""

