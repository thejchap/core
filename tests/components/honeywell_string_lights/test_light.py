"""Tryke skip-stubs for test_light.py - sibling port deferred (100 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (100 LOC, 0 parametrize)")
async def turn_on_off_sends_commands() -> None:
    """Stub for test_turn_on_off_sends_commands."""

@test.skip("sibling port deferred (100 LOC, 0 parametrize)")
async def restore_state() -> None:
    """Stub for test_restore_state."""

@test.skip("sibling port deferred (100 LOC, 0 parametrize)")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""
