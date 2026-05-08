"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry() -> None:
    """Stub for test_setup_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry_auth_failed() -> None:
    """Stub for test_setup_entry_auth_failed."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry_not_ready() -> None:
    """Stub for test_setup_entry_not_ready."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry_implementation_unavailable() -> None:
    """Stub for test_setup_entry_implementation_unavailable."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""

