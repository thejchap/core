"""Tryke skip stub for test_temperature_format.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def int_conversion() -> None:
    """Stub for test_int_conversion."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def rounding() -> None:
    """Stub for test_rounding."""

