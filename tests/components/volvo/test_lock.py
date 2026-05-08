"""Tryke skip stub for test_lock.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("volvo: sibling test pending tryke port")
async def lock() -> None:
    """Placeholder skipped sibling tests."""
