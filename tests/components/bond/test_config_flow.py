"""Tryke skip-stubs for bond config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_form() -> None:
    """Stub for test_user_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_form_can_create_when_already_discovered() -> None:
    """Stub for test_user_form_can_create_when_already_discovered (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_form_with_non_bridge() -> None:
    """Stub for test_user_form_with_non_bridge (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_form_invalid_auth() -> None:
    """Stub for test_user_form_invalid_auth (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_form_cannot_connect() -> None:
    """Stub for test_user_form_cannot_connect (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_form_old_firmware() -> None:
    """Stub for test_user_form_old_firmware (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_form_unexpected_client_error() -> None:
    """Stub for test_user_form_unexpected_client_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_form_unexpected_error() -> None:
    """Stub for test_user_form_unexpected_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_form_one_entry_per_device_allowed() -> None:
    """Stub for test_user_form_one_entry_per_device_allowed (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_form() -> None:
    """Stub for test_zeroconf_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def dhcp_discovery() -> None:
    """Stub for test_dhcp_discovery (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def dhcp_discovery_already_exists() -> None:
    """Stub for test_dhcp_discovery_already_exists (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def dhcp_discovery_short_name() -> None:
    """Stub for test_dhcp_discovery_short_name (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_form_token_unavailable() -> None:
    """Stub for test_zeroconf_form_token_unavailable (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_form_token_times_out() -> None:
    """Stub for test_zeroconf_form_token_times_out (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_form_with_token_available() -> None:
    """Stub for test_zeroconf_form_with_token_available (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_form_with_token_available_name_unavailable() -> None:
    """Stub for test_zeroconf_form_with_token_available_name_unavailable (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_already_configured() -> None:
    """Stub for test_zeroconf_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_in_setup_retry_state() -> None:
    """Stub for test_zeroconf_in_setup_retry_state (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_already_configured_refresh_token() -> None:
    """Stub for test_zeroconf_already_configured_refresh_token (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_already_configured_no_reload_same_host() -> None:
    """Stub for test_zeroconf_already_configured_no_reload_same_host (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_form_unexpected_error() -> None:
    """Stub for test_zeroconf_form_unexpected_error (port deferred)."""
