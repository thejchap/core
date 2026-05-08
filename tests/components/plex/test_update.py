"""Tryke skip-stubs for plex update tests.

Original tests use PlexAPI mocks + websocket + registry; full port deferred.
"""

from tryke import test

@test.skip("PlexAPI mocks + websocket + registry")
async def plex_update() -> None:
    """Test Plex update entity."""
