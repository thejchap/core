"""Tryke skip stub for test_helper.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("tado: sibling test pending tryke port — needs: indirect parametrize")
async def helper() -> None:
    """Placeholder skipped sibling tests."""
