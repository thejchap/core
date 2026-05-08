"""Tryke skip-stubs for plex playback tests.

Original tests use PlexAPI mocks + websocket + registry; full port deferred.
"""

from tryke import test

@test.skip("PlexAPI mocks + websocket + registry")
async def media_player_playback() -> None:
    """Test playing media on a Plex media_player."""
