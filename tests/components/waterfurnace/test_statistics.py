"""Tryke skip stub for test_statistics.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("waterfurnace: sibling test pending tryke port — needs: recorder_mock")
async def statistics() -> None:
    """Placeholder skipped sibling tests."""
