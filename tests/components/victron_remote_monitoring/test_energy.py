"""Tryke skip stub for test_energy.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("victron_remote_monitoring: sibling test pending tryke port — needs: conftest fixtures + sibling test infrastructure")
async def energy() -> None:
    """Placeholder skipped sibling tests."""
