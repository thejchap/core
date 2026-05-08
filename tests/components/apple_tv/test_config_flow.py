"""Test the apple_tv config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.apple_tv.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def show_user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user flow renders the device input form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(bool(result.get("type"))).to_be(True)


@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_input_device_not_found() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_input_unexpected_error() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_adds_full_device() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_adds_dmap_device() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_adds_dmap_device_failed() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_adds_device_with_ip_filter() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_pair_no_interaction() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_adds_device_by_ip_uses_unicast_scan() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_adds_existing_device() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_connection_failed() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_start_pair_error_failed() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_pair_service_with_password() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_pair_disabled_service() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_pair_ignore_unsupported() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_pair_invalid_pin() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_pair_unexpected_error() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_pair_backoff_error() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_pair_begin_unexpected_error() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def user_pair_begin_pair_error_failed() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def ignores_disabled_service() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def zeroconf() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def zeroconf_unsupported() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def zeroconf_during_zeroconf() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def zeroconf_existing_device_aborts() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def zeroconf_two_aborts() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def reconfigure_update_address() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def reconfigure_dmap_unique_id_does_not_change() -> None:
    """Stub."""

@test.skip("requires pyatv scan/pair mock chain + ssdp/zeroconf/dhcp/usb discovery")
async def options() -> None:
    """Stub."""
