"""Tryke skip stub for test_util.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("systemmonitor: sibling test pending tryke port — needs: complex parametrize")
async def util() -> None:
    """Placeholder skipped sibling tests."""
