"""Tryke skip stub for test_satellite.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("wyoming: sibling test pending tryke port — needs: conftest fixtures + sibling test infrastructure")
async def satellite() -> None:
    """Placeholder skipped sibling tests."""
