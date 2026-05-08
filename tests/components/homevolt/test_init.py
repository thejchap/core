"""Tryke skip-stubs for test_init.py - sibling port deferred (58 LOC, 1 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (58 LOC, 1 parametrize)")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry."""

@test.skip("sibling port deferred (58 LOC, 1 parametrize)")
async def config_entry_setup_failure() -> None:
    """Stub for test_config_entry_setup_failure."""
