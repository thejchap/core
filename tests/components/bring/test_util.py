"""Tryke skip stub for test_util.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def list_language() -> None:
    """Stub for test_list_language."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sum_attributes() -> None:
    """Stub for test_sum_attributes."""

