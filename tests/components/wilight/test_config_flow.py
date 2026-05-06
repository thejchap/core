"""Test the WiLight config flow."""

import dataclasses
from unittest.mock import patch

from pywilight.const import DOMAIN
from tryke import Depends, expect, fixture, test

from homeassistant.components.wilight.config_flow import (
    CONF_MODEL_NAME,
    CONF_SERIAL_NUMBER,
)
from homeassistant.config_entries import SOURCE_SSDP
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    CONF_COMPONENTS,
    HOST,
    MOCK_SSDP_DISCOVERY_INFO_MISSING_MANUFACTURER,
    MOCK_SSDP_DISCOVERY_INFO_P_B,
    MOCK_SSDP_DISCOVERY_INFO_WRONG_MANUFACTURER,
    UPNP_MODEL_NAME_P_B,
    UPNP_SERIAL,
    WILIGHT_ID,
)
from ._fixtures import (
    dummy_get_components_from_model_clear,
    dummy_get_components_from_model_wrong,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def show_ssdp_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the ssdp confirmation form is served."""

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO_P_B)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_SSDP}, data=discovery_info
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(result["description_placeholders"]).to_equal(
        {
            CONF_NAME: f"WL{WILIGHT_ID}",
            CONF_COMPONENTS: "light",
        }
    )


@test
async def ssdp_not_wilight_abort_1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the ssdp aborts not_wilight."""

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO_WRONG_MANUFACTURER)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_SSDP}, data=discovery_info
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_wilight_device")


@test
async def ssdp_not_wilight_abort_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the ssdp aborts not_wilight."""

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO_MISSING_MANUFACTURER)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_SSDP}, data=discovery_info
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_wilight_device")


@test
async def ssdp_not_wilight_abort_3(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _components: list = Depends(dummy_get_components_from_model_clear),
) -> None:
    """Test that the ssdp aborts not_wilight."""

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO_P_B)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_SSDP}, data=discovery_info
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_wilight_device")


@test
async def ssdp_not_supported_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _components: list = Depends(dummy_get_components_from_model_wrong),
) -> None:
    """Test that the ssdp aborts not_supported."""

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO_P_B)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_SSDP}, data=discovery_info
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_supported_device")


@test
async def ssdp_device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test abort SSDP flow if WiLight already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=WILIGHT_ID,
        data={
            CONF_HOST: HOST,
            CONF_SERIAL_NUMBER: UPNP_SERIAL,
            CONF_MODEL_NAME: UPNP_MODEL_NAME_P_B,
        },
    )

    entry.add_to_hass(hass)

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO_P_B)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def full_ssdp_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the full SSDP flow from start to finish."""

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO_P_B)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_SSDP}, data=discovery_info
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(result["description_placeholders"]).to_equal(
        {
            CONF_NAME: f"WL{WILIGHT_ID}",
            "components": "light",
        }
    )

    with patch("homeassistant.components.wilight.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"WL{WILIGHT_ID}")

    expect(bool(result["data"])).to_be(True)
    expect(result["data"][CONF_HOST]).to_equal(HOST)
    expect(result["data"][CONF_SERIAL_NUMBER]).to_equal(UPNP_SERIAL)
    expect(result["data"][CONF_MODEL_NAME]).to_equal(UPNP_MODEL_NAME_P_B)
