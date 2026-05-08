"""Tryke skip stub for test_backup.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("synology_dsm: sibling test pending tryke port — needs: ws client, hass_client")
async def backup() -> None:
    """Placeholder skipped sibling tests."""
