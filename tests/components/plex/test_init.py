"""Tryke skip-stubs for plex init tests.

Original tests use PlexAPI mocks + websocket + registry; full port deferred.
"""

from tryke import test

@test.skip("PlexAPI mocks + websocket + registry")
async def set_config_entry_unique_id() -> None:
    """Test updating missing unique_id from config entry."""

@test.skip("PlexAPI mocks + websocket + registry")
async def setup_config_entry_with_error() -> None:
    """Test setup component from config entry with errors."""

@test.skip("PlexAPI mocks + websocket + registry")
async def setup_with_insecure_config_entry() -> None:
    """Test setup component with config."""

@test.skip("PlexAPI mocks + websocket + registry")
async def unload_config_entry() -> None:
    """Test unloading a config entry."""

@test.skip("PlexAPI mocks + websocket + registry")
async def setup_with_photo_session() -> None:
    """Test setup component with config."""

@test.skip("PlexAPI mocks + websocket + registry")
async def setup_with_live_tv_session() -> None:
    """Test setup component with a Live TV session."""

@test.skip("PlexAPI mocks + websocket + registry")
async def setup_with_transient_session() -> None:
    """Test setup component with a transient session."""

@test.skip("PlexAPI mocks + websocket + registry")
async def setup_with_unknown_session() -> None:
    """Test setup component with an unknown session."""

@test.skip("PlexAPI mocks + websocket + registry")
async def setup_when_certificate_changed() -> None:
    """Test setup component when the Plex certificate has changed."""

@test.skip("PlexAPI mocks + websocket + registry")
async def tokenless_server() -> None:
    """Test setup with a server with token auth disabled."""

@test.skip("PlexAPI mocks + websocket + registry")
async def bad_token_with_tokenless_server() -> None:
    """Test setup with a bad token and a server with token auth disabled."""

@test.skip("PlexAPI mocks + websocket + registry")
async def scan_clients_schedule() -> None:
    """Test scan_clients scheduled update."""

@test.skip("PlexAPI mocks + websocket + registry")
async def setup_with_limited_credentials() -> None:
    """Test setup with a user with limited permissions."""

@test.skip("PlexAPI mocks + websocket + registry")
async def trigger_reauth() -> None:
    """Test setup and reauthorization of a Plex token."""

@test.skip("PlexAPI mocks + websocket + registry")
async def setup_with_deauthorized_token() -> None:
    """Test setup with a deauthorized token."""
