"""Tryke skip stub for test_number.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_params() -> None:
    """Stub for test_setup_params."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def default_setup_params() -> None:
    """Stub for test_default_setup_params."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def set_value_bad_attr() -> None:
    """Stub for test_set_value_bad_attr."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def set_value_bad_range() -> None:
    """Stub for test_set_value_bad_range."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def set_set_value() -> None:
    """Stub for test_set_set_value."""

