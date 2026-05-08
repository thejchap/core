"""Tryke skip-stubs for test_init.py - sibling port deferred (80 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (80 LOC, 0 parametrize)")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""

@test.skip("sibling port deferred (80 LOC, 0 parametrize)")
async def migrate_entry() -> None:
    """Stub for test_migrate_entry."""
