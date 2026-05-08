"""Tryke skip-stubs for test_event.py - sibling port deferred (66 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (66 LOC, 0 parametrize)")
async def door_bell_event() -> None:
    """Stub for test_door_bell_event."""

@test.skip("sibling port deferred (66 LOC, 0 parametrize)")
async def door_bell_event_wrong_event_type() -> None:
    """Stub for test_door_bell_event_wrong_event_type."""
