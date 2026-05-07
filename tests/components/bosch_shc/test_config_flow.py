"""Tryke skip-stubs for bosch_shc config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_user() -> None:
    """Stub for test_form_user (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_get_info_connection_error() -> None:
    """Stub for test_form_get_info_connection_error (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_get_info_exception() -> None:
    """Stub for test_form_get_info_exception (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_pairing_error() -> None:
    """Stub for test_form_pairing_error (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_user_invalid_auth() -> None:
    """Stub for test_form_user_invalid_auth (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_validate_connection_error() -> None:
    """Stub for test_form_validate_connection_error (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_validate_session_error() -> None:
    """Stub for test_form_validate_session_error (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_validate_exception() -> None:
    """Stub for test_form_validate_exception (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_already_configured() -> None:
    """Stub for test_form_already_configured (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def zeroconf() -> None:
    """Stub for test_zeroconf (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def zeroconf_already_configured() -> None:
    """Stub for test_zeroconf_already_configured (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def zeroconf_cannot_connect() -> None:
    """Stub for test_zeroconf_cannot_connect (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def zeroconf_not_bosch_shc() -> None:
    """Stub for test_zeroconf_not_bosch_shc (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reauth() -> None:
    """Stub for test_reauth (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def tls_assets_writer() -> None:
    """Stub for test_tls_assets_writer (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def register_multiple_controllers() -> None:
    """Stub for test_register_multiple_controllers (port deferred)."""
