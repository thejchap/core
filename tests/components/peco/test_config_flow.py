"""Test the PECO Outage Counter config flow."""

from __future__ import annotations

from unittest.mock import patch

from peco import HttpError, IncompatibleMeterError, UnresponsiveMeterError
from tryke import Depends, expect, fixture, test
from voluptuous.error import Invalid

from homeassistant import config_entries
from homeassistant.components.peco.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.peco.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"county": "PHILADELPHIA"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Philadelphia Outage Count")
    expect(result2["data"]).to_equal({"county": "PHILADELPHIA"})
    expect(result2["context"]["unique_id"]).to_equal("PHILADELPHIA")


@test
async def invalid_county(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test the InvalidCounty error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    raised: type[Exception] | None = None
    with patch(
        "homeassistant.components.peco.async_setup_entry",
        return_value=True,
    ):
        try:
            await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {"county": "INVALID_COUNTY_THAT_SHOULDNT_EXIST"},
            )
        except Invalid:
            raised = Invalid
    expect(raised).to_be(Invalid)


@test
async def meter_value_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test the MeterValueError path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "county": "PHILADELPHIA",
            "phone_number": "INVALID_SMART_METER_THAT_SHOULD_NOT_EXIST",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"phone_number": "invalid_phone_number"})


@test
async def incompatible_meter_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test the IncompatibleMeter error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch("peco.PecoOutageApi.meter_check", side_effect=IncompatibleMeterError()):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"county": "PHILADELPHIA", "phone_number": "1234567890"},
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("incompatible_meter")


@test
async def unresponsive_meter_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test the UnresponsiveMeter error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch("peco.PecoOutageApi.meter_check", side_effect=UnresponsiveMeterError()):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"county": "PHILADELPHIA", "phone_number": "1234567890"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"phone_number": "unresponsive_meter"})


@test
async def meter_http_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test the HttpError path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch("peco.PecoOutageApi.meter_check", side_effect=HttpError):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"county": "PHILADELPHIA", "phone_number": "1234567890"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"phone_number": "http_error"})


@test
async def smart_meter(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test the Smart Meter step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch("peco.PecoOutageApi.meter_check", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"county": "PHILADELPHIA", "phone_number": "1234567890"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Philadelphia - 1234567890")
    expect(result["data"]["phone_number"]).to_equal("1234567890")
    expect(result["context"]["unique_id"]).to_equal("PHILADELPHIA-1234567890")
