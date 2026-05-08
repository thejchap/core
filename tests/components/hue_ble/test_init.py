"""Tryke skip-stubs for test_init.py - sibling port deferred (124 LOC, 1 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (124 LOC, 1 parametrize)")
async def setup_error() -> None:
    """Stub for test_setup_error."""

@test.skip("sibling port deferred (124 LOC, 1 parametrize)")
async def setup() -> None:
    """Stub for test_setup."""
