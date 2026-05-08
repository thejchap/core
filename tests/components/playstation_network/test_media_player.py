"""Tryke skip-stubs for playstation_network media player tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def media_player_placeholder() -> None:
    """Placeholder skipped sibling tests for test_media_player.py."""
