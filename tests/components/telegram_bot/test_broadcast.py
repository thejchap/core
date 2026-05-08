"""Tryke skip stub for test_broadcast.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("telegram_bot: sibling test pending tryke port — needs: conftest fixtures + sibling test infrastructure")
async def broadcast() -> None:
    """Placeholder skipped sibling tests."""
