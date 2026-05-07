"""Tryke skip-stubs for eheimdigital config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def full_flow() -> None:
    """Stub for test_full_flow (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def flow_errors() -> None:
    """Stub for test_flow_errors (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def zeroconf_flow() -> None:
    """Stub for test_zeroconf_flow (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def zeroconf_flow_errors() -> None:
    """Stub for test_zeroconf_flow_errors (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def abort() -> None:
    """Stub for test_abort (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reconfigure() -> None:
    """Stub for test_reconfigure (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reconfigure_different_device() -> None:
    """Stub for test_reconfigure_different_device (port deferred)."""
