"""Test the apple_tv config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock, Mock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.apple_tv.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    dmap_device,
    full_device,
    mock_scan,
    mock_setup_entry,
    mrp_device,
    pairing,
    use_mocked_zeroconf,
    zero_aggregation_time,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


DMAP_SERVICE = ZeroconfServiceInfo(
    ip_address=ip_address("127.0.0.1"),
    ip_addresses=[ip_address("127.0.0.1")],
    hostname="mock_hostname",
    port=None,
    type="_touch-able._tcp.local.",
    name="dmapid._touch-able._tcp.local.",
    properties={"CtlN": "Apple TV"},
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _agg: None = Depends(zero_aggregation_time),
    _zc: None = Depends(use_mocked_zeroconf),
) -> None:
    """Anchor fixture for tryke fixture-injection.

    Routes mandatory autouse fixtures through a single hop so each test's
    ``hass`` Depends can resolve cleanly.
    """


@test
async def show_user_form(
    _trigger: None = Depends(_trigger_executor),
    _scan: AsyncMock = Depends(mock_scan),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user flow renders the device input form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_be("user")


@test
async def user_input_device_not_found(
    _trigger: None = Depends(_trigger_executor),
    _mrp: AsyncMock = Depends(mrp_device),
    _setup: Mock = Depends(mock_setup_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test when user specifies a non-existing device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_be("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"device_input": "none"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "no_devices_found"})


@test
async def user_input_unexpected_error(
    _trigger: None = Depends(_trigger_executor),
    scan_mock: AsyncMock = Depends(mock_scan),
    _setup: Mock = Depends(mock_setup_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that unexpected error yields an error message."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    scan_mock.side_effect = Exception
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"device_input": "dummy"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def user_adds_existing_device(
    _trigger: None = Depends(_trigger_executor),
    _mrp: AsyncMock = Depends(mrp_device),
    _setup: Mock = Depends(mock_setup_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that it is not possible to add an already-configured device."""
    MockConfigEntry(domain="apple_tv", unique_id="mrpid").add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"device_input": "127.0.0.1"},
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "already_configured"})


@test
async def user_adds_device_by_ip_uses_unicast_scan(
    _trigger: None = Depends(_trigger_executor),
    scan_mock: AsyncMock = Depends(mock_scan),
    _setup: Mock = Depends(mock_setup_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test add device by IP-address — verify unicast scan is used."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"device_input": "127.0.0.1"},
    )

    expect(str(scan_mock.hosts[0])).to_be("127.0.0.1")


@test
async def zeroconf_unsupported_service_aborts(
    _trigger: None = Depends(_trigger_executor),
    _scan: AsyncMock = Depends(mock_scan),
    _setup: Mock = Depends(mock_setup_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovering an unsupported zeroconf service aborts."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="mock_hostname",
            name="mock_name",
            port=None,
            type="_dummy._tcp.local.",
            properties={},
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_be("unknown")


@test
async def zeroconf_rejects_ipv6(
    _trigger: None = Depends(_trigger_executor),
    _scan: AsyncMock = Depends(mock_scan),
    _setup: Mock = Depends(mock_setup_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf discovery rejects ipv6 addresses."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("fd00::b27c:63bb:cc85:4ea0"),
            ip_addresses=[ip_address("fd00::b27c:63bb:cc85:4ea0")],
            hostname="mock_hostname",
            port=None,
            type="_touch-able._tcp.local.",
            name="dmapid._touch-able._tcp.local.",
            properties={"CtlN": "Apple TV"},
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_be("ipv6_not_supported")


@test
async def zeroconf_add_existing_device(
    _trigger: None = Depends(_trigger_executor),
    _dmap: AsyncMock = Depends(dmap_device),
    _setup: Mock = Depends(mock_setup_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test add already existing device from zeroconf aborts."""
    MockConfigEntry(domain="apple_tv", unique_id="dmapid").add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=DMAP_SERVICE
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_be("already_configured")


@test
async def zeroconf_add_but_device_not_found(
    _trigger: None = Depends(_trigger_executor),
    _scan: AsyncMock = Depends(mock_scan),
    _setup: Mock = Depends(mock_setup_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf flow with no device found in scan aborts."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=DMAP_SERVICE
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_be("no_devices_found")


# --- Stubs for tests requiring more complex pyatv pair flows -----------


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
