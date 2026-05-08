"""Tryke skip stub for test_switch.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("wake_on_lan: sibling test pending tryke port — needs: conftest fixtures + sibling test infrastructure")
async def switch() -> None:
    """Placeholder skipped sibling tests."""
