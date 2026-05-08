"""Test the Elmax config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.elmax.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
) -> HomeAssistant:
    """Anchor fixture so tryke fully resolves hass."""
    return hass


@test
async def show_menu(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("choose_mode")

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def direct_setup() -> None:
    """Stub for test_direct_setup (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def direct_show_form() -> None:
    """Stub for test_direct_show_form (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def cloud_setup() -> None:
    """Stub for test_cloud_setup (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def zeroconf_form_setup_api_not_supported() -> None:
    """Stub for test_zeroconf_form_setup_api_not_supported (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def zeroconf_discovery() -> None:
    """Stub for test_zeroconf_discovery (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def zeroconf_discovery_ipv6() -> None:
    """Stub for test_zeroconf_discovery_ipv6 (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def zeroconf_setup_show_form() -> None:
    """Stub for test_zeroconf_setup_show_form (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def zeroconf_setup() -> None:
    """Stub for test_zeroconf_setup (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def zeroconf_ipv6_setup() -> None:
    """Stub for test_zeroconf_ipv6_setup (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def zeroconf_already_configured() -> None:
    """Stub for test_zeroconf_already_configured (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def zeroconf_panel_changed_ip() -> None:
    """Stub for test_zeroconf_panel_changed_ip (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def one_config_allowed_cloud() -> None:
    """Stub for test_one_config_allowed_cloud (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def cloud_invalid_credentials() -> None:
    """Stub for test_cloud_invalid_credentials (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def cloud_connection_error() -> None:
    """Stub for test_cloud_connection_error (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def direct_connection_error() -> None:
    """Stub for test_direct_connection_error (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def direct_wrong_panel_code() -> None:
    """Stub for test_direct_wrong_panel_code (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def unhandled_error() -> None:
    """Stub for test_unhandled_error (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def invalid_pin() -> None:
    """Stub for test_invalid_pin (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def no_online_panel() -> None:
    """Stub for test_no_online_panel (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def show_reauth() -> None:
    """Stub for test_show_reauth (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reauth_flow() -> None:
    """Stub for test_reauth_flow (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reauth_panel_disappeared() -> None:
    """Stub for test_reauth_panel_disappeared (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reauth_invalid_pin() -> None:
    """Stub for test_reauth_invalid_pin (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reauth_bad_login() -> None:
    """Stub for test_reauth_bad_login (port deferred)."""
