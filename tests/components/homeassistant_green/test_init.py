"""Tryke skip-stubs for test_init.py - sibling port deferred (108 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (108 LOC, 0 parametrize)")
async def setup_entry() -> None:
    """Stub for test_setup_entry."""

@test.skip("sibling port deferred (108 LOC, 0 parametrize)")
async def setup_entry_no_hassio() -> None:
    """Stub for test_setup_entry_no_hassio."""

@test.skip("sibling port deferred (108 LOC, 0 parametrize)")
async def setup_entry_wrong_board() -> None:
    """Stub for test_setup_entry_wrong_board."""

@test.skip("sibling port deferred (108 LOC, 0 parametrize)")
async def setup_entry_wait_hassio() -> None:
    """Stub for test_setup_entry_wait_hassio."""
