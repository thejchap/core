"""Tests for the Sonos Media Player platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def plex_play_media() -> None:
    """Stub for test_plex_play_media (port deferred)."""
