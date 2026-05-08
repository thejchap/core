"""Tryke skip stub for test_select.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def select() -> None:
    """Stub for test_select."""

