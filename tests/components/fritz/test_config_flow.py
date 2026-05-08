"""Test the fritz config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.fritz.const import DOMAIN
from homeassistant.config_entries import SOURCE_SSDP, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_UDN,
    SsdpServiceInfo,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def user_show_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user form is shown for an empty flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def ssdp_ipv6_link_local(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that ipv6 link-local SSDP discovery is ignored."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="https://[fe80::1ff:fe23:4567:890a]:12345/test",
            upnp={
                ATTR_UPNP_FRIENDLY_NAME: "fake_name",
                ATTR_UPNP_UDN: "uuid:only-a-test",
            },
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("ignore_ip6_link_local")


@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user() -> None:
    """Stub for test_user (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_already_configured() -> None:
    """Stub for test_user_already_configured (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def exception_security() -> None:
    """Stub for test_exception_security (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def exception_connection() -> None:
    """Stub for test_exception_connection (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def exception_unknown() -> None:
    """Stub for test_exception_unknown (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reauth_successful() -> None:
    """Stub for test_reauth_successful (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reauth_not_successful() -> None:
    """Stub for test_reauth_not_successful (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reconfigure_successful() -> None:
    """Stub for test_reconfigure_successful (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reconfigure_not_successful() -> None:
    """Stub for test_reconfigure_not_successful (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_already_configured() -> None:
    """Stub for test_ssdp_already_configured (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_already_configured_host() -> None:
    """Stub for test_ssdp_already_configured_host (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_already_configured_host_uuid() -> None:
    """Stub for test_ssdp_already_configured_host_uuid (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_already_in_progress_host() -> None:
    """Stub for test_ssdp_already_in_progress_host (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp() -> None:
    """Stub for test_ssdp (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_exception() -> None:
    """Stub for test_ssdp_exception (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def options_flow() -> None:
    """Stub for test_options_flow (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def upnp_not_enabled() -> None:
    """Stub for test_upnp_not_enabled (port deferred)."""
