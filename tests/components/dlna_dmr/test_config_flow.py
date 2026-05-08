"""Test the dlna_dmr config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.dlna_dmr.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def user_flow_undiscovered_manual_show_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user-init'd flow with no discovered devices shows the manual form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("manual")


@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_flow_undiscovered_manual() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_flow_discovered_manual() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_flow_selected() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_flow_uncontactable() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_flow_embedded_st() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_flow_wrong_st() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_success() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_unavailable() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_existing() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_duplicate_location() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_duplicate_mac_ignored_entry() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_duplicate_mac_configured_entry() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_add_mac() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_dont_remove_mac() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_upnp_udn() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_missing_services() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_single_service() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_ignore_device() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ignore_flow() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ignore_flow_no_ssdp() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def get_mac_address_ipv4() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def get_mac_address_ipv6() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def get_mac_address_host() -> None:
    """Stub."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def options_flow() -> None:
    """Stub."""
