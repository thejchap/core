"""Tryke skip stub for test_fan.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("wilight: sibling test pending tryke port — needs: conftest fixtures + sibling test infrastructure")
async def fan() -> None:
    """Placeholder skipped sibling tests."""
