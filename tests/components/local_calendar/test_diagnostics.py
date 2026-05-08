"""Tryke skip-stubs for test_diagnostics.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def empty_calendar() -> None:
    """Stub for test_empty_calendar."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def api_date_time_event() -> None:
    """Stub for test_api_date_time_event."""
