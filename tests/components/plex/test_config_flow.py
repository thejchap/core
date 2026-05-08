"""Tryke skip-stubs for plex config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def bad_credentials() -> None:
    """Stub for test_bad_credentials (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def bad_hostname() -> None:
    """Stub for test_bad_hostname (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def unknown_exception() -> None:
    """Stub for test_unknown_exception (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def no_servers_found() -> None:
    """Stub for test_no_servers_found (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def single_available_server() -> None:
    """Stub for test_single_available_server (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def multiple_servers_with_selection() -> None:
    """Stub for test_multiple_servers_with_selection (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def adding_last_unconfigured_server() -> None:
    """Stub for test_adding_last_unconfigured_server (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def all_available_servers_configured() -> None:
    """Stub for test_all_available_servers_configured (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def option_flow() -> None:
    """Stub for test_option_flow (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def missing_option_flow() -> None:
    """Stub for test_missing_option_flow (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def option_flow_new_users_available() -> None:
    """Stub for test_option_flow_new_users_available (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def external_timed_out() -> None:
    """Stub for test_external_timed_out (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def callback_view() -> None:
    """Stub for test_callback_view (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def manual_config() -> None:
    """Stub for test_manual_config (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def manual_config_with_token() -> None:
    """Stub for test_manual_config_with_token (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def integration_discovery() -> None:
    """Stub for test_integration_discovery (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def reauth() -> None:
    """Stub for test_reauth (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def reauth_multiple_servers_available() -> None:
    """Stub for test_reauth_multiple_servers_available (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def client_request_missing() -> None:
    """Stub for test_client_request_missing (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def client_header_issues() -> None:
    """Stub for test_client_header_issues (port deferred)."""
