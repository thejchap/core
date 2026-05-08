"""Tryke skip-stubs for test_init.py - sibling port deferred (41 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (41 LOC, 0 parametrize)")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry."""

@test.skip("sibling port deferred (41 LOC, 0 parametrize)")
async def initialization_failure() -> None:
    """Stub for test_initialization_failure."""
