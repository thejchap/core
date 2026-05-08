"""Tryke skip stub for test_vacuum.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("tplink: sibling test pending tryke port")
async def vacuum() -> None:
    """Placeholder skipped sibling tests."""
