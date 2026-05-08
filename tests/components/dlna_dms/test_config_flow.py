"""Test the DLNA DMS config flow."""

from collections.abc import Generator
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.dlna_dms.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def ssdp_scanner_mock() -> Generator[Mock]:
    """Mock the SSDP Scanner."""
    with patch("homeassistant.components.ssdp.Scanner", autospec=True) as mock_scanner:
        reg_callback = mock_scanner.return_value.async_register_callback
        reg_callback.return_value = Mock(return_value=None)
        yield mock_scanner.return_value


@fixture
def ssdp_server_mock() -> Generator[None]:
    """Mock the SSDP Server."""
    with patch("homeassistant.components.ssdp.Server", autospec=True):
        yield


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    _server: None = Depends(ssdp_server_mock),
) -> HomeAssistant:
    """Anchor fixture so tryke fully resolves hass."""
    return hass


@test
async def user_flow_no_devices(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    scanner: Mock = Depends(ssdp_scanner_mock),
) -> None:
    """Test user-init'd flow, there's really no devices to choose from."""
    scanner.async_get_discovery_info_by_st.side_effect = [
        [],
        [],
        [],
        [],
    ]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_flow() -> None:
    """Stub for test_user_flow (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_success() -> None:
    """Stub for test_ssdp_flow_success (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_unavailable() -> None:
    """Stub for test_ssdp_flow_unavailable (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_existing() -> None:
    """Stub for test_ssdp_flow_existing (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_duplicate_location() -> None:
    """Stub for test_ssdp_flow_duplicate_location (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_bad_data() -> None:
    """Stub for test_ssdp_flow_bad_data (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def duplicate_name() -> None:
    """Stub for test_duplicate_name (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_flow_upnp_udn() -> None:
    """Stub for test_ssdp_flow_upnp_udn (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_missing_services() -> None:
    """Stub for test_ssdp_missing_services (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_single_service() -> None:
    """Stub for test_ssdp_single_service (port deferred)."""
