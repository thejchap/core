"""Tryke skip-stubs for plex button tests.

Original tests use PlexAPI mocks + websocket + registry; full port deferred.
"""

from tryke import test

@test.skip("PlexAPI mocks + websocket + registry")
async def scan_clients_button_schedule() -> None:
    """Test scan_clients button scheduled update."""
