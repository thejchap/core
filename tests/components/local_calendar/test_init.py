"""Tryke skip-stubs for test_init.py - sibling port deferred (60 LOC, 1 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (60 LOC, 1 parametrize)")
async def load_unload() -> None:
    """Stub for test_load_unload."""

@test.skip("sibling port deferred (60 LOC, 1 parametrize)")
async def remove_config_entry() -> None:
    """Stub for test_remove_config_entry."""

@test.skip("sibling port deferred (60 LOC, 1 parametrize)")
async def load_failure() -> None:
    """Stub for test_load_failure."""
