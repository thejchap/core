"""Tryke skip stub for test_repairs.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("workday: sibling test pending tryke port — needs: ws client, hass_client")
async def repairs() -> None:
    """Placeholder skipped sibling tests."""
