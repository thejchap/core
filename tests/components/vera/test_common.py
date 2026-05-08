"""Tryke skip stub for test_common.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("vera: sibling test pending tryke port — needs: conftest fixtures + sibling test infrastructure")
async def common() -> None:
    """Placeholder skipped sibling tests."""
