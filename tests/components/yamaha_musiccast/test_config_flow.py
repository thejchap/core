"""Test config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.yamaha_musiccast.const import DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_MODEL_NAME,
    ATTR_UPNP_SERIAL,
    SsdpServiceInfo,
)

from ._fixtures import (
    mock_empty_discovery_information,
    mock_get_device_info_exception,
    mock_get_device_info_invalid,
    mock_get_device_info_mc_exception,
    mock_get_device_info_valid,
    mock_setup_entry,
    mock_ssdp_no_yamaha,
    mock_ssdp_yamaha,
    mock_valid_discovery_information,
    silent_ssdp_scanner,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _ssdp: None = Depends(silent_ssdp_scanner),
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


# User Flows


@test
async def user_input_device_not_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _info: None = Depends(mock_get_device_info_mc_exception),
) -> None:
    """Test when user specifies a non-existing device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"host": "none"},
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def user_input_non_yamaha_device_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _info: None = Depends(mock_get_device_info_invalid),
) -> None:
    """Test when user specifies an existing device, which does not provide the musiccast API."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"host": "127.0.0.1"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "no_musiccast_device"})


@test
async def user_input_device_already_existing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _info: None = Depends(mock_get_device_info_valid),
) -> None:
    """Test when user specifies an existing device."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="1234567890",
        data={CONF_HOST: "192.168.188.18", "model": "MC20", "serial": "1234567890"},
    )
    mock_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"host": "192.168.188.18"},
    )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def user_input_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _info: None = Depends(mock_get_device_info_exception),
) -> None:
    """Test when user specifies an existing device, which does not provide the musiccast API."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"host": "127.0.0.1"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def user_input_device_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _info: None = Depends(mock_get_device_info_valid),
    _disco: None = Depends(mock_valid_discovery_information),
) -> None:
    """Test when user specifies an existing device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"host": "127.0.0.1"},
    )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(isinstance(result2["result"], ConfigEntry)).to_be(True)
    expect(result2["data"]).to_equal(
        {
            "host": "127.0.0.1",
            "serial": "1234567890",
            "upnp_description": "http://127.0.0.1:9000/MediaRenderer/desc.xml",
        }
    )


@test
async def user_input_device_found_no_ssdp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _info: None = Depends(mock_get_device_info_valid),
    _disco: None = Depends(mock_empty_discovery_information),
) -> None:
    """Test when user specifies an existing device, which no discovery data are present for."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"host": "127.0.0.1"},
    )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(isinstance(result2["result"], ConfigEntry)).to_be(True)
    expect(result2["data"]).to_equal(
        {
            "host": "127.0.0.1",
            "serial": "1234567890",
            "upnp_description": "http://127.0.0.1:49154/MediaRenderer/desc.xml",
        }
    )


# SSDP Flows


@test
async def ssdp_discovery_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _ssdp: None = Depends(mock_ssdp_no_yamaha),
) -> None:
    """Test when an SSDP discovered device is not a musiccast device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://127.0.0.1/desc.xml",
            upnp={
                ATTR_UPNP_MODEL_NAME: "MC20",
                ATTR_UPNP_SERIAL: "123456789",
            },
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("yxc_control_url_missing")


@test
async def ssdp_discovery_successful_add_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _ssdp: None = Depends(mock_ssdp_yamaha),
) -> None:
    """Test when the SSDP discovered device is a musiccast device and the user confirms it."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://127.0.0.1/desc.xml",
            upnp={
                ATTR_UPNP_MODEL_NAME: "MC20",
                ATTR_UPNP_SERIAL: "1234567890",
            },
        ),
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)
    expect(result["step_id"]).to_equal("confirm")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(isinstance(result2["result"], ConfigEntry)).to_be(True)
    expect(result2["data"]).to_equal(
        {
            "host": "127.0.0.1",
            "serial": "1234567890",
            "upnp_description": "http://127.0.0.1/desc.xml",
        }
    )


@test
async def ssdp_discovery_existing_device_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _ssdp: None = Depends(mock_ssdp_yamaha),
) -> None:
    """Test when the SSDP discovered device is a musiccast device, but it already exists with another IP."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="1234567890",
        data={CONF_HOST: "192.168.188.18", "model": "MC20", "serial": "1234567890"},
    )
    mock_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://127.0.0.1/desc.xml",
            upnp={
                ATTR_UPNP_MODEL_NAME: "MC20",
                ATTR_UPNP_SERIAL: "1234567890",
            },
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(mock_entry.data[CONF_HOST]).to_equal("127.0.0.1")
    expect(mock_entry.data["upnp_description"]).to_equal("http://127.0.0.1/desc.xml")
