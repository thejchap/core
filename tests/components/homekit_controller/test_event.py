"""Tryke skip-stubs for test_event.py - sibling port deferred (195 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (195 LOC, 0 parametrize)")
async def remote() -> None:
    """Stub for test_remote."""

@test.skip("sibling port deferred (195 LOC, 0 parametrize)")
async def button() -> None:
    """Stub for test_button."""

@test.skip("sibling port deferred (195 LOC, 0 parametrize)")
async def doorbell() -> None:
    """Stub for test_doorbell."""
