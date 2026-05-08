"""Tryke skip-stubs for test_select.py - sibling port deferred (94 LOC, 1 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (94 LOC, 1 parametrize)")
async def select_states() -> None:
    """Stub for test_select_states."""

@test.skip("sibling port deferred (94 LOC, 1 parametrize)")
async def select_commands() -> None:
    """Stub for test_select_commands."""
