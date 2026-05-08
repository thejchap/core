"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry_account_error() -> None:
    """Stub for test_setup_entry_account_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry_session_error() -> None:
    """Stub for test_setup_entry_session_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""

