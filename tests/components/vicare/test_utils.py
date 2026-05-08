"""Tryke skip stub for test_utils.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("vicare: sibling test pending tryke port — needs: complex parametrize")
async def utils() -> None:
    """Placeholder skipped sibling tests."""
