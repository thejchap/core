"""Tests for Pegel Online config flow."""

from __future__ import annotations

from unittest.mock import patch

from aiohttp.client_exceptions import ClientError
from tryke import Depends, expect, fixture, test

from homeassistant.components.pegel_online.const import CONF_STATION, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_RADIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import PegelOnlineMock
from .const import MOCK_CONFIG_ENTRY_DATA_DRESDEN, MOCK_NEARBY_STATIONS

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


MOCK_USER_DATA_STEP1 = {
    CONF_LOCATION: {CONF_LATITUDE: 51.0, CONF_LONGITUDE: 13.0},
    CONF_RADIUS: 25,
}

MOCK_USER_DATA_STEP2 = {CONF_STATION: "70272185-xxxx-xxxx-xxxx-43bea330dcae"}


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def user(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test starting a flow by user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.pegel_online.async_setup_entry", return_value=True
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.pegel_online.config_flow.PegelOnline",
        ) as pegelonline,
    ):
        pegelonline.return_value = PegelOnlineMock(nearby_stations=MOCK_NEARBY_STATIONS)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA_STEP1
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("select_station")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA_STEP2
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"][CONF_STATION]).to_equal(
            "70272185-xxxx-xxxx-xxxx-43bea330dcae"
        )
        expect(result["title"]).to_equal("DRESDEN ELBE")

        await hass.async_block_till_done()

    expect(mock_setup_entry.called).to_be(True)


@test
async def user_already_configured(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test starting a flow by user with an already configured station."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG_ENTRY_DATA_DRESDEN,
        unique_id=MOCK_CONFIG_ENTRY_DATA_DRESDEN[CONF_STATION],
    )
    mock_config.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.pegel_online.config_flow.PegelOnline",
    ) as pegelonline:
        pegelonline.return_value = PegelOnlineMock(nearby_stations=MOCK_NEARBY_STATIONS)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA_STEP1
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("select_station")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA_STEP2
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def connection_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test connection error during user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.pegel_online.async_setup_entry", return_value=True
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.pegel_online.config_flow.PegelOnline",
        ) as pegelonline,
    ):
        pegelonline.return_value = PegelOnlineMock(side_effect=ClientError)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA_STEP1
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]["base"]).to_equal("cannot_connect")

        pegelonline.return_value = PegelOnlineMock(nearby_stations=MOCK_NEARBY_STATIONS)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA_STEP1
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("select_station")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA_STEP2
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"][CONF_STATION]).to_equal(
            "70272185-xxxx-xxxx-xxxx-43bea330dcae"
        )
        expect(result["title"]).to_equal("DRESDEN ELBE")

        await hass.async_block_till_done()

    expect(mock_setup_entry.called).to_be(True)


@test
async def user_no_stations(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test starting a flow by user which does not find any station."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.pegel_online.async_setup_entry", return_value=True
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.pegel_online.config_flow.PegelOnline",
        ) as pegelonline,
    ):
        pegelonline.return_value = PegelOnlineMock(nearby_stations={})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA_STEP1
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"][CONF_RADIUS]).to_equal("no_stations")

        pegelonline.return_value = PegelOnlineMock(nearby_stations=MOCK_NEARBY_STATIONS)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA_STEP1
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("select_station")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA_STEP2
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"][CONF_STATION]).to_equal(
            "70272185-xxxx-xxxx-xxxx-43bea330dcae"
        )
        expect(result["title"]).to_equal("DRESDEN ELBE")

        await hass.async_block_till_done()

    expect(mock_setup_entry.called).to_be(True)
