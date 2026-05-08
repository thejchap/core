"""Tryke skip-stubs for test_events.py - sibling port deferred (116 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (116 LOC, 0 parametrize)")
async def knx_event() -> None:
    """Stub for test_knx_event."""

@test.skip("sibling port deferred (116 LOC, 0 parametrize)")
async def event_data() -> None:
    """Stub for test_event_data."""
