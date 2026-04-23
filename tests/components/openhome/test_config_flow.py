"""Tests for the Openhome config flow module."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components.openhome.const import DOMAIN
from homeassistant.config_entries import SOURCE_SSDP
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_UDN,
    SsdpServiceInfo,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_UDN = "uuid:4c494e4e-1234-ab12-abcd-01234567819f"
MOCK_FRIENDLY_NAME = "Test Client"
MOCK_SSDP_LOCATION = "http://device:12345/description.xml"

MOCK_DISCOVER = SsdpServiceInfo(
    ssdp_usn="usn",
    ssdp_st="st",
    ssdp_location=MOCK_SSDP_LOCATION,
    upnp={ATTR_UPNP_FRIENDLY_NAME: MOCK_FRIENDLY_NAME, ATTR_UPNP_UDN: MOCK_UDN},
)


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def ssdp(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test a ssdp import flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=MOCK_DISCOVER,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(result["description_placeholders"]).to_equal({CONF_NAME: MOCK_FRIENDLY_NAME})

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result2["title"]).to_equal(MOCK_FRIENDLY_NAME)
    expect(result2["data"]).to_equal({CONF_HOST: MOCK_SSDP_LOCATION})


@test
async def device_exists(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test a ssdp import where device already exists."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: MOCK_SSDP_LOCATION},
        title=MOCK_FRIENDLY_NAME,
        unique_id=MOCK_UDN,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=MOCK_DISCOVER,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def missing_udn(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test a ssdp import where discovery is missing udn."""
    broken_discovery = SsdpServiceInfo(
        ssdp_usn="usn",
        ssdp_st="st",
        ssdp_location=MOCK_SSDP_LOCATION,
        upnp={
            ATTR_UPNP_FRIENDLY_NAME: MOCK_FRIENDLY_NAME,
        },
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=broken_discovery,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("incomplete_discovery")


@test
async def missing_ssdp_location(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test a ssdp import where discovery is missing udn."""
    broken_discovery = SsdpServiceInfo(
        ssdp_usn="usn",
        ssdp_st="st",
        ssdp_location="",
        upnp={ATTR_UPNP_FRIENDLY_NAME: MOCK_FRIENDLY_NAME, ATTR_UPNP_UDN: MOCK_UDN},
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=broken_discovery,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("incomplete_discovery")


@test
async def host_updated(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test a ssdp import flow where host changes."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "old_host"},
        title=MOCK_FRIENDLY_NAME,
        unique_id=MOCK_UDN,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=MOCK_DISCOVER,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(entry.data[CONF_HOST]).to_equal(MOCK_SSDP_LOCATION)
