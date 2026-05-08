"""Tryke skip stub for test_views.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("unifiprotect: sibling test pending tryke port")
async def views() -> None:
    """Placeholder skipped sibling tests."""
