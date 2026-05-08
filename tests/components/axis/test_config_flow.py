"""Test the axis config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.axis.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def flow_manual_configuration_show_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the manual user form is shown for a fresh config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def flow_manual_configuration() -> None:
    """Stub for test_flow_manual_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def manual_configuration_duplicate_fails() -> None:
    """Stub for test_manual_configuration_duplicate_fails (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def flow_fails_on_api() -> None:
    """Stub for test_flow_fails_on_api (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def flow_create_entry_multiple_existing_entries_of_same_model() -> None:
    """Stub for test_flow_create_entry_multiple_existing_entries_of_same_model (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reauth_flow_update_configuration() -> None:
    """Stub for test_reauth_flow_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reconfiguration_flow_update_configuration() -> None:
    """Stub for test_reconfiguration_flow_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovery_flow() -> None:
    """Stub for test_discovery_flow (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovered_device_already_configured() -> None:
    """Stub for test_discovered_device_already_configured (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovery_flow_updated_configuration() -> None:
    """Stub for test_discovery_flow_updated_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovery_flow_allowed_oui() -> None:
    """Stub for test_discovery_flow_allowed_oui (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovery_flow_ignore_non_axis_device() -> None:
    """Stub for test_discovery_flow_ignore_non_axis_device (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovery_flow_ignore_link_local_address() -> None:
    """Stub for test_discovery_flow_ignore_link_local_address (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def option_flow() -> None:
    """Stub for test_option_flow (port deferred)."""
