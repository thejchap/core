"""Tryke skip-stubs for plex services tests.

Original tests use PlexAPI mocks + websocket + registry; full port deferred.
"""

from tryke import test

@test.skip("PlexAPI mocks + websocket + registry")
async def refresh_library() -> None:
    """Test refresh_library service call."""

@test.skip("PlexAPI mocks + websocket + registry")
async def lookup_media_for_other_integrations() -> None:
    """Test media lookup for media_player.play_media calls from cast/sonos."""

@test.skip("PlexAPI mocks + websocket + registry")
async def lookup_media_with_urls() -> None:
    """Test media lookup for media_player.play_media calls from cast/sonos."""
