"""Tryke skip-stubs for crownstone config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def no_user_input() -> None:
    """Stub for test_no_user_input (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def abort_if_configured() -> None:
    """Stub for test_abort_if_configured (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def authentication_errors() -> None:
    """Stub for test_authentication_errors (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def unknown_error() -> None:
    """Stub for test_unknown_error (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def successful_login_no_usb() -> None:
    """Stub for test_successful_login_no_usb (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def successful_login_with_usb() -> None:
    """Stub for test_successful_login_with_usb (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def successful_login_with_manual_usb_path() -> None:
    """Stub for test_successful_login_with_manual_usb_path (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def options_flow_setup_usb() -> None:
    """Stub for test_options_flow_setup_usb (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def options_flow_remove_usb() -> None:
    """Stub for test_options_flow_remove_usb (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def options_flow_manual_usb_path() -> None:
    """Stub for test_options_flow_manual_usb_path (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def options_flow_change_usb_sphere() -> None:
    """Stub for test_options_flow_change_usb_sphere (port deferred)."""
