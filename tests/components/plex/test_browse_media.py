"""Tryke skip-stubs for plex browse_media tests.

Original tests use PlexAPI mocks + websocket + registry; full port deferred.
"""

from tryke import test

@test.skip("PlexAPI mocks + websocket + registry")
async def browse_media() -> None:
    """Test getting Plex clients from plex.tv."""
