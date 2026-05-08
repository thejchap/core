"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unload_config_entry() -> None:
    """Stub for test_unload_config_entry."""

