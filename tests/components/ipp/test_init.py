"""Tryke skip-stubs for test_init.py - sibling port deferred (45 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (45 LOC, 0 parametrize)")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""

@test.skip("sibling port deferred (45 LOC, 0 parametrize)")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry."""
