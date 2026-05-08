"""Tryke skip-stubs for plex media_search tests.

Original tests use PlexAPI mocks + websocket + registry; full port deferred.
"""

from tryke import test

@test.skip("PlexAPI mocks + websocket + registry")
async def media_lookups() -> None:
    """Test media lookups to Plex server."""
