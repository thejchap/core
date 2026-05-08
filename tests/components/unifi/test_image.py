"""Tryke skip stub for test_image.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("unifi: sibling test pending tryke port — needs: syrupy snapshot, hass_client")
async def image() -> None:
    """Placeholder skipped sibling tests."""
