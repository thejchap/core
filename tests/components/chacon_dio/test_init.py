"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def cover_unload_entry() -> None:
    """Stub for test_cover_unload_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def cover_shutdown_event() -> None:
    """Stub for test_cover_shutdown_event."""

