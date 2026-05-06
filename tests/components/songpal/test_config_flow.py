"""Test the songpal config flow."""

from __future__ import annotations

import copy
import dataclasses
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.songpal.const import CONF_ENDPOINT, DOMAIN
from homeassistant.config_entries import (
    SOURCE_IMPORT,
    SOURCE_SSDP,
    SOURCE_USER,
    ConfigFlowResult,
)
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_UDN,
    SsdpServiceInfo,
)

from . import (
    CONF_DATA,
    ENDPOINT,
    FRIENDLY_NAME,
    HOST,
    MODEL,
    _create_mocked_device,
    _patch_config_flow_device,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

UDN = "uuid:1234"

SSDP_DATA = SsdpServiceInfo(
    ssdp_usn="mock_usn",
    ssdp_st="mock_st",
    ssdp_location=f"http://{HOST}:52323/dmr.xml",
    upnp={
        ATTR_UPNP_UDN: UDN,
        ATTR_UPNP_FRIENDLY_NAME: FRIENDLY_NAME,
        "X_ScalarWebAPI_DeviceInfo": {
            "X_ScalarWebAPI_BaseURL": ENDPOINT,
            "X_ScalarWebAPI_ServiceList": {
                "X_ScalarWebAPI_ServiceType": [
                    "guide",
                    "system",
                    "audio",
                    "avContent",
                ],
            },
        },
    },
)


def _flow_next(hass: HomeAssistant, flow_id: str) -> ConfigFlowResult:
    return next(
        flow
        for flow in hass.config_entries.flow.async_progress()
        if flow["flow_id"] == flow_id
    )


def _patch_setup():
    return patch(
        "homeassistant.components.songpal.async_setup_entry",
        return_value=True,
    )


def _create_mock_config_entry(hass: HomeAssistant) -> None:
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="uuid:0000",
        data=CONF_DATA,
    ).add_to_hass(hass)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def flow_ssdp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test working ssdp flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=SSDP_DATA
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    expect(result["description_placeholders"]).to_equal(
        {CONF_NAME: FRIENDLY_NAME, CONF_HOST: HOST}
    )
    flow = _flow_next(hass, result["flow_id"])
    expect(flow["context"]["unique_id"]).to_equal(UDN)

    with _patch_setup():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(FRIENDLY_NAME)
        expect(result["data"]).to_equal(CONF_DATA)


@test
async def flow_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test working user initialized flow."""
    mocked_device = _create_mocked_device()

    with _patch_config_flow_device(mocked_device), _patch_setup():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_be(None)
        _flow_next(hass, result["flow_id"])

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ENDPOINT: ENDPOINT}
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(MODEL)
        expect(result["data"]).to_equal({CONF_NAME: MODEL, CONF_ENDPOINT: ENDPOINT})

    mocked_device.get_supported_methods.assert_called_once()
    mocked_device.get_interface_information.assert_called_once()


@test
async def flow_import(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test working import flow."""
    mocked_device = _create_mocked_device()

    with _patch_config_flow_device(mocked_device), _patch_setup():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=CONF_DATA
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(FRIENDLY_NAME)
        expect(result["data"]).to_equal(CONF_DATA)

    mocked_device.get_supported_methods.assert_called_once()
    mocked_device.get_interface_information.assert_not_called()


@test
async def flow_import_without_name(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test import flow without optional name."""
    mocked_device = _create_mocked_device()

    with _patch_config_flow_device(mocked_device), _patch_setup():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data={CONF_ENDPOINT: ENDPOINT}
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(MODEL)
        expect(result["data"]).to_equal({CONF_NAME: MODEL, CONF_ENDPOINT: ENDPOINT})

    mocked_device.get_supported_methods.assert_called_once()
    mocked_device.get_interface_information.assert_called_once()


@test
async def ssdp_bravia(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovering a bravia TV."""
    ssdp_data = dataclasses.replace(SSDP_DATA)
    ssdp_data.upnp = copy.deepcopy(ssdp_data.upnp)
    ssdp_data.upnp["X_ScalarWebAPI_DeviceInfo"]["X_ScalarWebAPI_ServiceList"][
        "X_ScalarWebAPI_ServiceType"
    ].append("videoScreen")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=ssdp_data
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_songpal_device")


@test
async def sddp_exist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovering existed device."""
    _create_mock_config_entry(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=SSDP_DATA
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_exist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user adding existed device."""
    mocked_device = _create_mocked_device()
    _create_mock_config_entry(hass)

    with _patch_config_flow_device(mocked_device):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")

    mocked_device.get_supported_methods.assert_called_once()
    mocked_device.get_interface_information.assert_called_once()


@test
async def import_exist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test importing existed device."""
    mocked_device = _create_mocked_device()
    _create_mock_config_entry(hass)

    with _patch_config_flow_device(mocked_device):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=CONF_DATA
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")

    mocked_device.get_supported_methods.assert_called_once()
    mocked_device.get_interface_information.assert_not_called()


@test
async def user_invalid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test using adding invalid config."""
    mocked_device = _create_mocked_device(True)
    _create_mock_config_entry(hass)

    with _patch_config_flow_device(mocked_device):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mocked_device.get_supported_methods.assert_called_once()
    mocked_device.get_interface_information.assert_not_called()


@test
async def import_invalid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test importing invalid config."""
    mocked_device = _create_mocked_device(True)
    _create_mock_config_entry(hass)

    with _patch_config_flow_device(mocked_device):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=CONF_DATA
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("cannot_connect")

    mocked_device.get_supported_methods.assert_called_once()
    mocked_device.get_interface_information.assert_not_called()
