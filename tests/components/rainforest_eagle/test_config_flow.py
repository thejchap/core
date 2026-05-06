"""Test the Rainforest Eagle config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.rainforest_eagle.const import (
    CONF_CLOUD_ID,
    CONF_HARDWARE_ADDRESS,
    CONF_INSTALL_CODE,
    DOMAIN,
    TYPE_EAGLE_100,
    TYPE_EAGLE_200,
)
from homeassistant.components.rainforest_eagle.data import CannotConnect, InvalidAuth
from homeassistant.const import CONF_HOST, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


class _MockElectricMeter:
    def __init__(self, hardware_address: str, connection_status: str) -> None:
        self.hardware_address = hardware_address
        self.connection_status = connection_status


_USER_INPUT = {
    CONF_CLOUD_ID: "abcdef",
    CONF_INSTALL_CODE: "123456",
    CONF_HOST: "192.168.1.55",
}


@test
async def form_multiple_meters_first_connected(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test proper flow with an EAGLE-200 with multiple meters, one connected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    meters = [
        _MockElectricMeter("meter-1", "Not Joined"),
        _MockElectricMeter("meter-2", "Connected"),
        _MockElectricMeter("meter-3", "Not Joined"),
    ]

    with (
        patch("aioeagle.EagleHub.get_device_list", return_value=meters),
        patch(
            "homeassistant.components.rainforest_eagle.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], _USER_INPUT
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("abcdef")
    expect(result["data"]).to_equal(
        {
            CONF_TYPE: TYPE_EAGLE_200,
            CONF_HOST: "192.168.1.55",
            CONF_CLOUD_ID: "abcdef",
            CONF_INSTALL_CODE: "123456",
            CONF_HARDWARE_ADDRESS: "meter-2",
        }
    )
    expect(result["result"].unique_id).to_equal("abcdef")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_eagle_200_meters_none_connected(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test proper flow with an EAGLE-200 where all meters are disconnected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    meters = [
        _MockElectricMeter("meter-1", "Not Joined"),
        _MockElectricMeter("meter-2", "Not Joined"),
        _MockElectricMeter("meter-3", "Not Joined"),
    ]

    with patch("aioeagle.EagleHub.get_device_list", return_value=meters):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], _USER_INPUT
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "no_meters_connected"})


@test
async def form_eagle_200_no_meters(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test proper flow with an EAGLE-200 with an empty list of meters."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("aioeagle.EagleHub.get_device_list", return_value=[]):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], _USER_INPUT
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "no_meters_connected"})


@test
async def form_eagle_100(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test proper flow for EAGLE-100."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    eagle_100_response = {"NetworkInfo": {"ModelId": "Z109-EAGLE"}}

    with (
        patch("aioeagle.EagleHub.get_device_list", side_effect=KeyError),
        patch("eagle100.Eagle.get_network_info", return_value=eagle_100_response),
        patch(
            "homeassistant.core.HomeAssistant.async_add_executor_job",
            return_value=eagle_100_response,
        ),
        patch(
            "homeassistant.components.rainforest_eagle.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], _USER_INPUT
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("abcdef")
    expect(result["data"]).to_equal(
        {
            CONF_TYPE: TYPE_EAGLE_100,
            CONF_HOST: "192.168.1.55",
            CONF_CLOUD_ID: "abcdef",
            CONF_INSTALL_CODE: "123456",
            CONF_HARDWARE_ADDRESS: None,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_unknown_device_type(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test flow when device type cannot be determined."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    unknown_device_response = {"NetworkInfo": {"ModelId": "UNKNOWN-DEVICE"}}

    with (
        patch("aioeagle.EagleHub.get_device_list", side_effect=KeyError),
        patch(
            "eagle100.Eagle.get_network_info", return_value=unknown_device_response
        ),
        patch(
            "homeassistant.core.HomeAssistant.async_add_executor_job",
            return_value=unknown_device_response,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], _USER_INPUT
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown_device_type"})


@test
async def form_unsupported_device_type(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow when device type is unsupported."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.rainforest_eagle.config_flow.async_get_type",
        return_value=("UNSUPPORTED_DEVICE_TYPE", None),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], _USER_INPUT
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unsupported_device_type"})


@test
async def form_unexpected_exception(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow when an unexpected exception occurs."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.rainforest_eagle.config_flow.async_get_type",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], _USER_INPUT
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown"})


@test
async def form_invalid_auth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("aioeagle.EagleHub.get_device_list", side_effect=InvalidAuth):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], _USER_INPUT
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("aioeagle.EagleHub.get_device_list", side_effect=CannotConnect):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], _USER_INPUT
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})
