"""Tryke skip-stubs for flux_led config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovery() -> None:
    """Stub for test_discovery (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovery_legacy() -> None:
    """Stub for test_discovery_legacy (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovery_with_existing_device_present() -> None:
    """Stub for test_discovery_with_existing_device_present (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovery_no_device() -> None:
    """Stub for test_discovery_no_device (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def manual_working_discovery() -> None:
    """Stub for test_manual_working_discovery (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow_can_replace_ignored() -> None:
    """Stub for test_user_flow_can_replace_ignored (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def manual_no_discovery_data() -> None:
    """Stub for test_manual_no_discovery_data (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovered_by_discovery_and_dhcp() -> None:
    """Stub for test_discovered_by_discovery_and_dhcp (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovered_by_discovery() -> None:
    """Stub for test_discovered_by_discovery (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovered_by_dhcp_udp_responds() -> None:
    """Stub for test_discovered_by_dhcp_udp_responds (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovered_by_dhcp_no_udp_response() -> None:
    """Stub for test_discovered_by_dhcp_no_udp_response (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovered_by_dhcp_partial_udp_response_fallback_tcp() -> None:
    """Stub for test_discovered_by_dhcp_partial_udp_response_fallback_tcp (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovered_by_dhcp_no_udp_response_or_tcp_response() -> None:
    """Stub for test_discovered_by_dhcp_no_udp_response_or_tcp_response (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovered_by_dhcp_or_discovery_adds_missing_unique_id() -> None:
    """Stub for test_discovered_by_dhcp_or_discovery_adds_missing_unique_id (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def mac_address_off_by_one_updated_via_discovery() -> None:
    """Stub for test_mac_address_off_by_one_updated_via_discovery (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def mac_address_off_by_one_not_updated_from_dhcp() -> None:
    """Stub for test_mac_address_off_by_one_not_updated_from_dhcp (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovered_by_dhcp_or_discovery_mac_address_mismatch_host_already_configured() -> None:
    """Stub for test_discovered_by_dhcp_or_discovery_mac_address_mismatch_host_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def options() -> None:
    """Stub for test_options (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovered_can_be_ignored() -> None:
    """Stub for test_discovered_can_be_ignored (port deferred)."""
