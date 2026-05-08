"""Tryke skip stub for test_init.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("teltonika: sibling test pending tryke port — needs: syrupy snapshot")
async def init() -> None:
    """Placeholder skipped sibling tests."""
