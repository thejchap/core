"""Tryke skip stub for test_diagnostics.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("vesync: sibling test pending tryke port — needs: syrupy snapshot, hass_client")
async def diagnostics() -> None:
    """Placeholder skipped sibling tests."""
