"""Tryke skip stub for test_calendar.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def calendar_platform() -> None:
    """Stub for test_calendar_platform."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def api_events() -> None:
    """Stub for test_api_events."""

