"""Tryke skip-stubs for test_calendar.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def calendar_events() -> None:
    """Stub for test_calendar_events."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def calendar_edge_cases() -> None:
    """Stub for test_calendar_edge_cases."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def no_calendar_events_global_disable() -> None:
    """Stub for test_no_calendar_events_global_disable."""
