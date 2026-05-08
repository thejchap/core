"""Tryke skip-stubs for plex sensor tests.

Original tests use PlexAPI mocks + websocket + registry; full port deferred.
"""

from tryke import test

@test.skip("PlexAPI mocks + websocket + registry")
async def library_sensor_values() -> None:
    """Test the library sensors."""
