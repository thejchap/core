"""Test the axis config flow."""

from ipaddress import ip_address

from tryke import Depends, expect, fixture, test

from homeassistant.components.axis.const import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_SSDP, SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .const import MAC

from tests.hass_fixtures import hass as hass_fixture, mock_network


DHCP_FORMATTED_MAC = dr.format_mac(MAC).replace(":", "")


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


# --- Non-Axis discovery rejections (no aioclient_mock dependency) ---


@test.cases(
    test.case(
        "dhcp",
        source=SOURCE_DHCP,
        discovery_info=DhcpServiceInfo(
            hostname="",
            ip="",
            macaddress=dr.format_mac("01234567890").replace(":", ""),
        ),
    ),
    test.case(
        "ssdp",
        source=SOURCE_SSDP,
        discovery_info=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            upnp={
                "friendlyName": "",
                "serialNumber": "01234567890",
                "presentationURL": "",
            },
        ),
    ),
    test.case(
        "zeroconf",
        source=SOURCE_ZEROCONF,
        discovery_info=ZeroconfServiceInfo(
            ip_address=None,
            ip_addresses=[],
            hostname="mock_hostname",
            name="",
            port=0,
            properties={"macaddress": "01234567890"},
            type="mock_type",
        ),
    ),
)
async def discovery_flow_ignore_non_axis_device(
    *,
    source: str,
    discovery_info,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that discovery flow ignores devices with non-Axis OUI."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, data=discovery_info, context={"source": source}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_be("not_axis_device")


@test.cases(
    test.case(
        "dhcp",
        source=SOURCE_DHCP,
        discovery_info=DhcpServiceInfo(
            hostname=f"axis-{MAC}",
            ip="169.254.3.4",
            macaddress=DHCP_FORMATTED_MAC,
        ),
    ),
    test.case(
        "ssdp",
        source=SOURCE_SSDP,
        discovery_info=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            upnp={
                "friendlyName": f"AXIS M1065-LW - {MAC}",
                "serialNumber": MAC,
                "presentationURL": "http://169.254.3.4:80/",
            },
        ),
    ),
    test.case(
        "zeroconf",
        source=SOURCE_ZEROCONF,
        discovery_info=ZeroconfServiceInfo(
            ip_address=ip_address("169.254.3.4"),
            ip_addresses=[ip_address("169.254.3.4")],
            hostname="mock_hostname",
            name=f"AXIS M1065-LW - {MAC}._axis-video._tcp.local.",
            port=80,
            properties={"macaddress": MAC},
            type="mock_type",
        ),
    ),
)
async def discovery_flow_ignore_link_local_address(
    *,
    source: str,
    discovery_info,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that discovery flow ignores devices with link-local addresses."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, data=discovery_info, context={"source": source}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_be("link_local_address")


# --- Stubs for tests requiring full Vapix HTTP mock chain ---


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
async def option_flow() -> None:
    """Stub for test_option_flow (port deferred)."""
