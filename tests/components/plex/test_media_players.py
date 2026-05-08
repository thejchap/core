"""Tryke skip-stubs for plex media_players tests.

Original tests use PlexAPI mocks + websocket + registry; full port deferred.
"""

from tryke import test

@test.skip("PlexAPI mocks + websocket + registry")
async def plex_tv_clients() -> None:
    """Test getting Plex clients from plex.tv."""
