"""Tryke skip-stubs for dlna_dms config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_flow() -> None:
    """Stub for test_user_flow (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_flow_no_devices() -> None:
    """Stub for test_user_flow_no_devices (port deferred)."""

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
async def ssdp_flow_bad_data() -> None:
    """Stub for test_ssdp_flow_bad_data (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def duplicate_name() -> None:
    """Stub for test_duplicate_name (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_upnp_udn() -> None:
    """Stub for test_ssdp_flow_upnp_udn (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_missing_services() -> None:
    """Stub for test_ssdp_missing_services (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_single_service() -> None:
    """Stub for test_ssdp_single_service (port deferred)."""
