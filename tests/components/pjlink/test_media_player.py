"""Tryke skip-stubs for pjlink media player tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def media_player_placeholder() -> None:
    """Placeholder skipped sibling tests for test_media_player.py."""
