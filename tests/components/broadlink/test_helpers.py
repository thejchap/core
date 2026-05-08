"""Tryke skip stub for test_helpers.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def padding() -> None:
    """Stub for test_padding."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def valid_mac_address() -> None:
    """Stub for test_valid_mac_address."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def invalid_mac_address() -> None:
    """Stub for test_invalid_mac_address."""

