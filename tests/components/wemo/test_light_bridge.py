"""Tryke skip stub for test_light_bridge.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("wemo: sibling test pending tryke port — needs: conftest fixtures + sibling test infrastructure")
async def light_bridge() -> None:
    """Placeholder skipped sibling tests."""
