"""Tryke skip-stubs for test_init.py - sibling port deferred (81 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (81 LOC, 0 parametrize)")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""

@test.skip("sibling port deferred (81 LOC, 0 parametrize)")
async def unknown_error() -> None:
    """Stub for test_unknown_error."""

@test.skip("sibling port deferred (81 LOC, 0 parametrize)")
async def callrate_limit() -> None:
    """Stub for test_callrate_limit."""
