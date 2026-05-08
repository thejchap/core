"""Tryke skip stub for test_select.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_params() -> None:
    """Stub for test_setup_params."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def select_option_bad_attr() -> None:
    """Stub for test_select_option_bad_attr."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def select_option() -> None:
    """Stub for test_select_option."""

