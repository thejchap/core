"""Tryke skip stub for test_media_player.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("webostv: sibling test pending tryke port — needs: syrupy snapshot, hass_client, aioclient_mock")
async def media_player() -> None:
    """Placeholder skipped sibling tests."""
