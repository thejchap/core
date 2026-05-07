"""Tryke skip-stubs for dlna_dmr config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_flow_undiscovered_manual() -> None:
    """Stub for test_user_flow_undiscovered_manual (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_flow_discovered_manual() -> None:
    """Stub for test_user_flow_discovered_manual (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_flow_selected() -> None:
    """Stub for test_user_flow_selected (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_flow_uncontactable() -> None:
    """Stub for test_user_flow_uncontactable (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_flow_embedded_st() -> None:
    """Stub for test_user_flow_embedded_st (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_flow_wrong_st() -> None:
    """Stub for test_user_flow_wrong_st (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_success() -> None:
    """Stub for test_ssdp_flow_success (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_unavailable() -> None:
    """Stub for test_ssdp_flow_unavailable (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_existing() -> None:
    """Stub for test_ssdp_flow_existing (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_duplicate_location() -> None:
    """Stub for test_ssdp_flow_duplicate_location (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_duplicate_mac_ignored_entry() -> None:
    """Stub for test_ssdp_duplicate_mac_ignored_entry (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_duplicate_mac_configured_entry() -> None:
    """Stub for test_ssdp_duplicate_mac_configured_entry (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_add_mac() -> None:
    """Stub for test_ssdp_add_mac (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_dont_remove_mac() -> None:
    """Stub for test_ssdp_dont_remove_mac (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_upnp_udn() -> None:
    """Stub for test_ssdp_flow_upnp_udn (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_missing_services() -> None:
    """Stub for test_ssdp_missing_services (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_single_service() -> None:
    """Stub for test_ssdp_single_service (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_ignore_device() -> None:
    """Stub for test_ssdp_ignore_device (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ignore_flow() -> None:
    """Stub for test_ignore_flow (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ignore_flow_no_ssdp() -> None:
    """Stub for test_ignore_flow_no_ssdp (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def get_mac_address_ipv4() -> None:
    """Stub for test_get_mac_address_ipv4 (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def get_mac_address_ipv6() -> None:
    """Stub for test_get_mac_address_ipv6 (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def get_mac_address_host() -> None:
    """Stub for test_get_mac_address_host (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def options_flow() -> None:
    """Stub for test_options_flow (port deferred)."""
