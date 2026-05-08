"""Tryke skip stub for test_calendar.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def calendar() -> None:
    """Stub for test_calendar."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def get_events() -> None:
    """Stub for test_get_events."""


