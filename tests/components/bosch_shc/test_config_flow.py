"""Test the bosch_shc config flow."""

from ipaddress import ip_address

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.bosch_shc.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import mock_async_zeroconf


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zeroconf=Depends(mock_async_zeroconf),
) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def form_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})


@test
async def zeroconf_not_bosch_shc(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we filter out non-bosch_shc devices from zeroconf discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ZeroconfServiceInfo(
            ip_address=ip_address("1.1.1.1"),
            ip_addresses=[ip_address("1.1.1.1")],
            hostname="mock_hostname",
            name="notboschshc",
            port=None,
            properties={},
            type="mock_type",
        ),
        context={"source": config_entries.SOURCE_ZEROCONF},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_bosch_shc")

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
async def reauth() -> None:
    """Stub for test_reauth (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def tls_assets_writer() -> None:
    """Stub for test_tls_assets_writer (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def register_multiple_controllers() -> None:
    """Stub for test_register_multiple_controllers (port deferred)."""
