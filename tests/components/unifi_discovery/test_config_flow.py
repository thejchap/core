"""Test the UniFi Discovery config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.unifi_discovery.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo

from . import DEVICE_HOSTNAME, DEVICE_IP_ADDRESS, DEVICE_MAC_ADDRESS, _patch_discovery

from tests.hass_fixtures import hass as hass_fixture, mock_network

DHCP_DISCOVERY = DhcpServiceInfo(
    hostname=DEVICE_HOSTNAME,
    ip=DEVICE_IP_ADDRESS,
    macaddress=DEVICE_MAC_ADDRESS.lower().replace(":", ""),
)

SSDP_DISCOVERY = SsdpServiceInfo(
    ssdp_usn="mock_usn",
    ssdp_st="mock_st",
    upnp={
        "manufacturer": "Ubiquiti Networks",
        "modelDescription": "UniFi Dream Machine",
    },
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(
    test.case("dhcp", source=config_entries.SOURCE_DHCP, data=DHCP_DISCOVERY),
    test.case("ssdp", source=config_entries.SOURCE_SSDP, data=SSDP_DISCOVERY),
)
async def dhcp_ssdp_abort_with_discovery_started(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    source: str,
    data: DhcpServiceInfo | SsdpServiceInfo,
) -> None:
    """Test DHCP and SSDP discovery triggers scanner and aborts."""
    with _patch_discovery() as mock_scanner:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source},
            data=data,
        )
        await hass.async_block_till_done(wait_background_tasks=True)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("discovery_started")
    expect(mock_scanner.async_scan.call_count).to_equal(1)


@test.cases(
    test.case("dhcp", source=config_entries.SOURCE_DHCP, data=DHCP_DISCOVERY),
    test.case("ssdp", source=config_entries.SOURCE_SSDP, data=SSDP_DISCOVERY),
)
async def dhcp_ssdp_abort_already_in_progress(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    source: str,
    data: DhcpServiceInfo | SsdpServiceInfo,
) -> None:
    """Test DHCP and SSDP abort when another flow is already in progress."""
    with (
        _patch_discovery(),
        patch(
            "homeassistant.components.unifi_discovery.config_flow.UnifiDiscoveryFlowHandler._async_in_progress",
            return_value=[{"flow_id": "mock_flow"}],
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source},
            data=data,
        )
        await hass.async_block_till_done(wait_background_tasks=True)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_in_progress")


@test
async def user_flow_aborts(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user-initiated flow aborts."""
    with _patch_discovery() as mock_scanner:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        await hass.async_block_till_done(wait_background_tasks=True)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("discovery_started")
    expect(mock_scanner.async_scan.call_count).to_equal(1)
