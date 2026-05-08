"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remove_entry_while_loaded() -> None:
    """Stub for test_remove_entry_while_loaded."""

