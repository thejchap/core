"""Tryke skip stub for test_cover.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("switcher_kis: sibling test pending tryke port — needs: indirect parametrize")
async def cover() -> None:
    """Placeholder skipped sibling tests."""
