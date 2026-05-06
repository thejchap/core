"""Tests for syncthru config flow."""

from unittest.mock import AsyncMock

from pysyncthru import SyncThruAPINotSupported
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.syncthru.const import DOMAIN
from homeassistant.config_entries import SOURCE_SSDP, SOURCE_USER
from homeassistant.const import CONF_NAME, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_DEVICE_TYPE,
    ATTR_UPNP_MANUFACTURER,
    ATTR_UPNP_PRESENTATION_URL,
    ATTR_UPNP_SERIAL,
    ATTR_UPNP_UDN,
    SsdpServiceInfo,
)

from ._fixtures import mock_config_entry, mock_setup_entry, mock_syncthru

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

FIXTURE_USER_INPUT = {
    CONF_URL: "http://192.168.1.2/",
    CONF_NAME: "My Printer",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _syncthru: AsyncMock = Depends(mock_syncthru),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=FIXTURE_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(FIXTURE_USER_INPUT)
    expect(result["result"].unique_id).to_be(None)


@test
async def already_configured_by_url(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _syncthru: AsyncMock = Depends(mock_syncthru),
) -> None:
    """Test we match and update already configured devices by URL."""
    udn = "uuid:XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    MockConfigEntry(
        domain=DOMAIN,
        data={**FIXTURE_USER_INPUT, CONF_NAME: "Already configured"},
        title="Already configured",
        unique_id=udn,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=FIXTURE_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_URL]).to_equal(FIXTURE_USER_INPUT[CONF_URL])
    expect(result["data"][CONF_NAME]).to_equal(FIXTURE_USER_INPUT[CONF_NAME])
    expect(result["result"].unique_id).to_equal(udn)


@test
async def syncthru_not_supported(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    syncthru: AsyncMock = Depends(mock_syncthru),
) -> None:
    """Test we show user form on unsupported device."""
    syncthru.update.side_effect = SyncThruAPINotSupported
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=FIXTURE_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({CONF_URL: "syncthru_not_supported"})


@test
async def unknown_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    syncthru: AsyncMock = Depends(mock_syncthru),
) -> None:
    """Test we show user form on unsupported device."""
    syncthru.is_unknown_state.return_value = True
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=FIXTURE_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({CONF_URL: "unknown_state"})

    syncthru.is_unknown_state.return_value = False

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=FIXTURE_USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def ssdp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _syncthru: AsyncMock = Depends(mock_syncthru),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test SSDP discovery initiates config properly."""
    url = "http://192.168.1.2/"
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://192.168.1.2:5200/Printer.xml",
            upnp={
                ATTR_UPNP_DEVICE_TYPE: "urn:schemas-upnp-org:device:Printer:1",
                ATTR_UPNP_MANUFACTURER: "Samsung Electronics",
                ATTR_UPNP_PRESENTATION_URL: url,
                ATTR_UPNP_SERIAL: "00000000",
                ATTR_UPNP_UDN: "uuid:XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
            },
        ),
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(CONF_URL in result["data_schema"].schema).to_be(True)
    for k in result["data_schema"].schema:
        if k == CONF_URL:
            expect(k.default()).to_equal(url)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: url, CONF_NAME: "Printer"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_URL: url, CONF_NAME: "Printer"})
    expect(result["result"].unique_id).to_equal(
        "uuid:XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    )


@test
async def ssdp_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _syncthru: AsyncMock = Depends(mock_syncthru),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test SSDP discovery initiates config properly."""
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        config_entry, unique_id="uuid:XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    )

    url = "http://192.168.1.2/"
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://192.168.1.2:5200/Printer.xml",
            upnp={
                ATTR_UPNP_DEVICE_TYPE: "urn:schemas-upnp-org:device:Printer:1",
                ATTR_UPNP_MANUFACTURER: "Samsung Electronics",
                ATTR_UPNP_PRESENTATION_URL: url,
                ATTR_UPNP_SERIAL: "00000000",
                ATTR_UPNP_UDN: "uuid:XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
            },
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
