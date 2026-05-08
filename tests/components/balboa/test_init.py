"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry() -> None:
    """Stub for test_setup_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry_fails() -> None:
    """Stub for test_setup_entry_fails."""

