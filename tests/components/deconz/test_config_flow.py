"""Tryke skip-stubs for deconz config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def flow_discovered_bridges() -> None:
    """Stub for test_flow_discovered_bridges (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def flow_manual_configuration_decision() -> None:
    """Stub for test_flow_manual_configuration_decision (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def flow_manual_configuration() -> None:
    """Stub for test_flow_manual_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def manual_configuration_after_discovery_timeout() -> None:
    """Stub for test_manual_configuration_after_discovery_timeout (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def manual_configuration_after_discovery_ResponseError() -> None:
    """Stub for test_manual_configuration_after_discovery_ResponseError (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def manual_configuration_update_configuration() -> None:
    """Stub for test_manual_configuration_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def manual_configuration_dont_update_configuration() -> None:
    """Stub for test_manual_configuration_dont_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def manual_configuration_timeout_get_bridge() -> None:
    """Stub for test_manual_configuration_timeout_get_bridge (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def link_step_fails() -> None:
    """Stub for test_link_step_fails (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reauth_flow_update_configuration() -> None:
    """Stub for test_reauth_flow_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def flow_ssdp_discovery() -> None:
    """Stub for test_flow_ssdp_discovery (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_discovery_update_configuration() -> None:
    """Stub for test_ssdp_discovery_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_discovery_dont_update_configuration() -> None:
    """Stub for test_ssdp_discovery_dont_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_discovery_dont_update_existing_hassio_configuration() -> None:
    """Stub for test_ssdp_discovery_dont_update_existing_hassio_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def flow_hassio_discovery() -> None:
    """Stub for test_flow_hassio_discovery (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def hassio_discovery_update_configuration() -> None:
    """Stub for test_hassio_discovery_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def hassio_discovery_dont_update_configuration() -> None:
    """Stub for test_hassio_discovery_dont_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def option_flow() -> None:
    """Stub for test_option_flow (port deferred)."""
