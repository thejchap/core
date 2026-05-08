"""Tryke skip stub for test_calendar.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("withings: sibling test pending tryke port — needs: syrupy snapshot, hass_client")
async def calendar() -> None:
    """Placeholder skipped sibling tests."""
