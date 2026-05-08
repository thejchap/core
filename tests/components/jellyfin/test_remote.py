"""Tryke skip-stubs for test_remote.py - sibling port deferred (93 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (93 LOC, 0 parametrize)")
async def remote() -> None:
    """Stub for test_remote."""

@test.skip("sibling port deferred (93 LOC, 0 parametrize)")
async def services() -> None:
    """Stub for test_services."""
