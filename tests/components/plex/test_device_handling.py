"""Tryke skip-stubs for plex device_handling tests.

Original tests use PlexAPI mocks + websocket + registry; full port deferred.
"""

from tryke import test

@test.skip("PlexAPI mocks + websocket + registry")
async def cleanup_orphaned_devices() -> None:
    """Test cleaning up orphaned devices on startup."""

@test.skip("PlexAPI mocks + websocket + registry")
async def migrate_transient_devices() -> None:
    """Test cleaning up transient devices on startup."""
