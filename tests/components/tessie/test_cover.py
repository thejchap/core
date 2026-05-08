"""Tryke skip stub for test_cover.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("tessie: sibling test pending tryke port — needs: syrupy snapshot")
async def cover() -> None:
    """Placeholder skipped sibling tests."""
