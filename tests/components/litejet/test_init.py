"""Tryke skip-stubs for test_init.py - sibling port deferred (22 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (22 LOC, 0 parametrize)")
async def setup_with_no_config() -> None:
    """Stub for test_setup_with_no_config."""

@test.skip("sibling port deferred (22 LOC, 0 parametrize)")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""
