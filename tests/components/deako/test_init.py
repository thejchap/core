"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def deako_async_setup_entry() -> None:
    """Stub for test_deako_async_setup_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def deako_async_setup_entry_devices_error() -> None:
    """Stub for test_deako_async_setup_entry_devices_error."""

