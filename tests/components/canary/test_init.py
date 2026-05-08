"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def async_setup_raises_entry_not_ready() -> None:
    """Stub for test_async_setup_raises_entry_not_ready."""

