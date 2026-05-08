"""Tryke skip-stubs for test_switch.py - sibling port deferred (152 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (152 LOC, 0 parametrize)")
async def bluetooth() -> None:
    """Stub for test_bluetooth."""

@test.skip("sibling port deferred (152 LOC, 0 parametrize)")
async def switch_error() -> None:
    """Stub for test_switch_error."""

@test.skip("sibling port deferred (152 LOC, 0 parametrize)")
async def switch_connection_error() -> None:
    """Stub for test_switch_connection_error."""
