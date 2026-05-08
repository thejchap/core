"""Tryke skip stub for test_number.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def number_set_value() -> None:
    """Stub for test_number_set_value."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def number_set_invalid_value_caught_by_hass() -> None:
    """Stub for test_number_set_invalid_value_caught_by_hass."""

