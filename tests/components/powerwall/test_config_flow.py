"""Tryke skip-stubs for powerwall config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def form_source_user() -> None:
    """Stub for test_form_source_user (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def form_cannot_connect() -> None:
    """Stub for test_form_cannot_connect (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def invalid_auth() -> None:
    """Stub for test_invalid_auth (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def form_unknown_exception() -> None:
    """Stub for test_form_unknown_exception (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def form_wrong_version() -> None:
    """Stub for test_form_wrong_version (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def already_configured() -> None:
    """Stub for test_already_configured (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def already_configured_with_ignored() -> None:
    """Stub for test_already_configured_with_ignored (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def dhcp_discovery_manual_configure() -> None:
    """Stub for test_dhcp_discovery_manual_configure (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def dhcp_discovery_auto_configure() -> None:
    """Stub for test_dhcp_discovery_auto_configure (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def dhcp_discovery_cannot_connect() -> None:
    """Stub for test_dhcp_discovery_cannot_connect (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def form_reauth() -> None:
    """Stub for test_form_reauth (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def dhcp_discovery_update_ip_address() -> None:
    """Stub for test_dhcp_discovery_update_ip_address (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def dhcp_discovery_does_not_update_ip_when_auth_fails() -> None:
    """Stub for test_dhcp_discovery_does_not_update_ip_when_auth_fails (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def dhcp_discovery_does_not_update_ip_when_auth_successful() -> None:
    """Stub for test_dhcp_discovery_does_not_update_ip_when_auth_successful (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def dhcp_discovery_updates_unique_id() -> None:
    """Stub for test_dhcp_discovery_updates_unique_id (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def dhcp_discovery_updates_unique_id_when_entry_is_failed() -> None:
    """Stub for test_dhcp_discovery_updates_unique_id_when_entry_is_failed (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def discovered_wifi_does_not_update_ip_if_is_still_online() -> None:
    """Stub for test_discovered_wifi_does_not_update_ip_if_is_still_online (port deferred)."""

@test.skip("requires tesla_powerwall mock chain (not ported)")
async def discovered_wifi_does_not_update_ip_online_but_access_denied() -> None:
    """Stub for test_discovered_wifi_does_not_update_ip_online_but_access_denied (port deferred)."""
