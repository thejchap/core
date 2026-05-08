"""Tryke skip stub for test_number.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("vallox: sibling test pending tryke port — needs: complex parametrize")
async def number() -> None:
    """Placeholder skipped sibling tests."""
