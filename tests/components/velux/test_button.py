"""Tryke skip stub for test_button.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("velux: sibling test pending tryke port — needs: syrupy snapshot, indirect parametrize")
async def button() -> None:
    """Placeholder skipped sibling tests."""
