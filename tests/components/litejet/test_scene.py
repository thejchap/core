"""Tryke skip-stubs for test_scene.py - sibling port deferred (69 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (69 LOC, 0 parametrize)")
async def disabled_by_default() -> None:
    """Stub for test_disabled_by_default."""

@test.skip("sibling port deferred (69 LOC, 0 parametrize)")
async def activate() -> None:
    """Stub for test_activate."""

@test.skip("sibling port deferred (69 LOC, 0 parametrize)")
async def connected_event() -> None:
    """Stub for test_connected_event."""
