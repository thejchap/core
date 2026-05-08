"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry() -> None:
    """Stub for test_setup_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unload_entry_while_player_is_offline() -> None:
    """Stub for test_unload_entry_while_player_is_offline."""

