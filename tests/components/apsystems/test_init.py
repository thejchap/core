"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_failed() -> None:
    """Stub for test_setup_failed."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update() -> None:
    """Stub for test_update."""

