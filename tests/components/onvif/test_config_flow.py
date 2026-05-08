"""Tryke skip-stubs for onvif config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def flow_discovered_devices() -> None:
    """Stub for test_flow_discovered_devices (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def flow_discovered_devices_ignore_configured_manual_input() -> None:
    """Stub for test_flow_discovered_devices_ignore_configured_manual_input (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def flow_discovered_no_device() -> None:
    """Stub for test_flow_discovered_no_device (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def flow_discovery_ignore_existing_and_abort() -> None:
    """Stub for test_flow_discovery_ignore_existing_and_abort (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def flow_manual_entry() -> None:
    """Stub for test_flow_manual_entry (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def flow_manual_entry_no_profiles() -> None:
    """Stub for test_flow_manual_entry_no_profiles (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def flow_manual_entry_no_mac() -> None:
    """Stub for test_flow_manual_entry_no_mac (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def flow_manual_entry_fails() -> None:
    """Stub for test_flow_manual_entry_fails (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def flow_manual_entry_wrong_password() -> None:
    """Stub for test_flow_manual_entry_wrong_password (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def option_flow() -> None:
    """Stub for test_option_flow (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def discovered_by_dhcp_updates_host() -> None:
    """Stub for test_discovered_by_dhcp_updates_host (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def discovered_by_dhcp_does_nothing_if_host_is_the_same() -> None:
    """Stub for test_discovered_by_dhcp_does_nothing_if_host_is_the_same (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def discovered_by_dhcp_does_not_update_if_already_loaded() -> None:
    """Stub for test_discovered_by_dhcp_does_not_update_if_already_loaded (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def discovered_by_dhcp_does_not_update_if_no_matching_entry() -> None:
    """Stub for test_discovered_by_dhcp_does_not_update_if_no_matching_entry (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def form_reauth() -> None:
    """Stub for test_form_reauth (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def flow_manual_entry_updates_existing_user_password() -> None:
    """Stub for test_flow_manual_entry_updates_existing_user_password (port deferred)."""

@test.skip("requires onvif camera mock chain + DHCP/zeroconf discovery (not ported)")
async def flow_manual_entry_wrong_port() -> None:
    """Stub for test_flow_manual_entry_wrong_port (port deferred)."""
