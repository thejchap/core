"""Tryke skip stub for test_init.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("weheat: sibling test pending tryke port — needs: oauth credentials")
async def init() -> None:
    """Placeholder skipped sibling tests."""
