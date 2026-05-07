"""Tryke skip-stubs for bosch_alarm config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_user() -> None:
    """Stub for test_form_user (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_exceptions() -> None:
    """Stub for test_form_exceptions (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_exceptions_user() -> None:
    """Stub for test_form_exceptions_user (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def entry_already_configured_host() -> None:
    """Stub for test_entry_already_configured_host (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def entry_already_configured_serial() -> None:
    """Stub for test_entry_already_configured_serial (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def dhcp_can_finish() -> None:
    """Stub for test_dhcp_can_finish (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def dhcp_exceptions() -> None:
    """Stub for test_dhcp_exceptions (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def dhcp_updates_host() -> None:
    """Stub for test_dhcp_updates_host (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def dhcp_discovery_if_panel_setup_config_flow() -> None:
    """Stub for test_dhcp_discovery_if_panel_setup_config_flow (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def dhcp_abort_ongoing_flow() -> None:
    """Stub for test_dhcp_abort_ongoing_flow (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def dhcp_updates_mac() -> None:
    """Stub for test_dhcp_updates_mac (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reauth_flow_success() -> None:
    """Stub for test_reauth_flow_success (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reauth_flow_error() -> None:
    """Stub for test_reauth_flow_error (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reconfig_flow() -> None:
    """Stub for test_reconfig_flow (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reconfig_flow_incorrect_model() -> None:
    """Stub for test_reconfig_flow_incorrect_model (port deferred)."""
