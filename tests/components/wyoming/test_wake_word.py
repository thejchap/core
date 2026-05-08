"""Tryke skip stub for test_wake_word.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("wyoming: sibling test pending tryke port — needs: syrupy snapshot")
async def wake_word() -> None:
    """Placeholder skipped sibling tests."""
