"""Tryke skip-stubs for test_media_player.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("xbox: sibling test pending tryke port")
async def media_players() -> None:
    """Stub for test_media_players."""


@test.skip("xbox: sibling test pending tryke port")
async def browse_media() -> None:
    """Stub for test_browse_media."""


@test.skip("xbox: sibling test pending tryke port")
async def media_player_actions() -> None:
    """Stub for test_media_player_actions."""


@test.skip("xbox: sibling test pending tryke port")
async def media_player_action_exceptions() -> None:
    """Stub for test_media_player_action_exceptions."""


@test.skip("xbox: sibling test pending tryke port")
async def media_player_turn_on_failed() -> None:
    """Stub for test_media_player_turn_on_failed."""
