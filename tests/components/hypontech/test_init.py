"""Tryke skip-stubs for test_init.py - sibling port deferred (51 LOC, 1 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (51 LOC, 1 parametrize)")
async def setup_entry() -> None:
    """Stub for test_setup_entry."""

@test.skip("sibling port deferred (51 LOC, 1 parametrize)")
async def setup_and_unload_entry() -> None:
    """Stub for test_setup_and_unload_entry."""
