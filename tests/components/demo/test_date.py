"""Tryke skip stub for test_date.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_params() -> None:
    """Stub for test_setup_params."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def set_datetime() -> None:
    """Stub for test_set_datetime."""

