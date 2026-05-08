"""Tryke skip-stubs for nrgkick config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def user_flow() -> None:
    """Stub for test_user_flow (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def user_flow_with_credentials() -> None:
    """Stub for test_user_flow_with_credentials (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def form_invalid_host_input() -> None:
    """Stub for test_form_invalid_host_input (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def form_fallback_title_when_device_name_missing() -> None:
    """Stub for test_form_fallback_title_when_device_name_missing (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def form_invalid_response_when_serial_missing() -> None:
    """Stub for test_form_invalid_response_when_serial_missing (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def user_flow_errors() -> None:
    """Stub for test_user_flow_errors (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def user_flow_auth_errors() -> None:
    """Stub for test_user_flow_auth_errors (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def user_already_configured() -> None:
    """Stub for test_user_already_configured (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def user_auth_already_configured() -> None:
    """Stub for test_user_auth_already_configured (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def zeroconf_discovery() -> None:
    """Stub for test_zeroconf_discovery (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def zeroconf_discovery_with_credentials() -> None:
    """Stub for test_zeroconf_discovery_with_credentials (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def zeroconf_errors() -> None:
    """Stub for test_zeroconf_errors (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def zeroconf_already_configured() -> None:
    """Stub for test_zeroconf_already_configured (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def zeroconf_json_api_disabled() -> None:
    """Stub for test_zeroconf_json_api_disabled (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def zeroconf_json_api_disabled_stale_mdns() -> None:
    """Stub for test_zeroconf_json_api_disabled_stale_mdns (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def zeroconf_json_api_disabled_errors() -> None:
    """Stub for test_zeroconf_json_api_disabled_errors (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def zeroconf_json_api_disabled_with_credentials() -> None:
    """Stub for test_zeroconf_json_api_disabled_with_credentials (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def zeroconf_enable_json_api_auth_errors() -> None:
    """Stub for test_zeroconf_enable_json_api_auth_errors (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def zeroconf_auth_errors() -> None:
    """Stub for test_zeroconf_auth_errors (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def zeroconf_no_serial_number() -> None:
    """Stub for test_zeroconf_no_serial_number (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def reauth_flow() -> None:
    """Stub for test_reauth_flow (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def reauth_flow_errors() -> None:
    """Stub for test_reauth_flow_errors (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def reauth_flow_unique_id_mismatch() -> None:
    """Stub for test_reauth_flow_unique_id_mismatch (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def reconfigure_flow() -> None:
    """Stub for test_reconfigure_flow (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def reconfigure_flow_with_credentials() -> None:
    """Stub for test_reconfigure_flow_with_credentials (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def reconfigure_flow_errors() -> None:
    """Stub for test_reconfigure_flow_errors (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def reconfigure_flow_auth_errors() -> None:
    """Stub for test_reconfigure_flow_auth_errors (port deferred)."""

@test.skip("requires mock_nrgkick_api + JSON fixtures + zeroconf chain (not ported)")
async def reconfigure_flow_unique_id_mismatch() -> None:
    """Stub for test_reconfigure_flow_unique_id_mismatch (port deferred)."""
