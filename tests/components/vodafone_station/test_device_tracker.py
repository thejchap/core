"""Tryke skip stub for test_device_tracker.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("vodafone_station: sibling test pending tryke port — needs: syrupy snapshot")
async def device_tracker() -> None:
    """Placeholder skipped sibling tests."""
