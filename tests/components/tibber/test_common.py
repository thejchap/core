"""Tryke skip stub for test_common.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("tibber: sibling test pending tryke port")
async def common() -> None:
    """Placeholder skipped sibling tests."""
