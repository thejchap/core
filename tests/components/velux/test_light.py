"""Tryke skip stub for test_light.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("velux: sibling test pending tryke port — needs: syrupy snapshot, indirect parametrize")
async def light() -> None:
    """Placeholder skipped sibling tests."""
