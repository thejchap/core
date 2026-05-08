"""Tryke skip stub for test_util.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("teltonika: sibling test pending tryke port — needs: conftest fixtures + sibling test infrastructure")
async def util() -> None:
    """Placeholder skipped sibling tests."""
