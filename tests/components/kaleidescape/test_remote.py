"""Tryke skip-stubs for test_remote.py - sibling port deferred (145 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (145 LOC, 0 parametrize)")
async def entity() -> None:
    """Stub for test_entity."""

@test.skip("sibling port deferred (145 LOC, 0 parametrize)")
async def commands() -> None:
    """Stub for test_commands."""

@test.skip("sibling port deferred (145 LOC, 0 parametrize)")
async def unknown_command() -> None:
    """Stub for test_unknown_command."""
