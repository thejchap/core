"""Tryke skip-stubs for test_calendar.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def calendar_state_off() -> None:
    """Stub for test_calendar_state_off."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def calendar_state_on() -> None:
    """Stub for test_calendar_state_on."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def empty_calendar() -> None:
    """Stub for test_empty_calendar."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def calendar_snapshot() -> None:
    """Stub for test_calendar_snapshot."""
