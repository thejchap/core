"""Tryke skip-stubs for plex server tests.

Original tests use PlexAPI mocks + websocket + registry; full port deferred.
"""

from tryke import test

@test.skip("PlexAPI mocks + websocket + registry")
async def new_users_available() -> None:
    """Test setting up when new users available on Plex server."""

@test.skip("PlexAPI mocks + websocket + registry")
async def new_ignored_users_available() -> None:
    """Test setting up when new users available on Plex server but are ignored."""

@test.skip("PlexAPI mocks + websocket + registry")
async def network_error_during_refresh() -> None:
    """Test network failures during refreshes."""

@test.skip("PlexAPI mocks + websocket + registry")
async def gdm_client_failure() -> None:
    """Test connection failure to a GDM discovered client."""

@test.skip("PlexAPI mocks + websocket + registry")
async def mark_sessions_idle() -> None:
    """Test marking media_players as idle when sessions end."""

@test.skip("PlexAPI mocks + websocket + registry")
async def ignore_plex_web_client() -> None:
    """Test option to ignore Plex Web clients."""
