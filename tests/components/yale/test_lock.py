"""Tryke skip stub for test_lock.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("yale: sibling test pending tryke port — needs: syrupy snapshot")
async def lock() -> None:
    """Placeholder skipped sibling tests."""
