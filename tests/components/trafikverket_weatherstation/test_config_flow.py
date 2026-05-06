"""Test the Trafikverket weatherstation config flow."""

from __future__ import annotations

from unittest.mock import patch

from pytrafikverket.exceptions import (
    InvalidAuthentication,
    MultipleWeatherStationsFound,
    NoWeatherStationFound,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DOMAIN = "trafikverket_weatherstation"
CONF_STATION = "station"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.trafikverket_weatherstation.config_flow.TrafikverketWeather.async_get_weather",
        ),
        patch(
            "homeassistant.components.trafikverket_weatherstation.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "1234567890",
                CONF_STATION: "Vallby",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Vallby")
    expect(result2["data"]).to_equal(
        {
            "api_key": "1234567890",
            "station": "Vallby",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", side_effect=InvalidAuthentication, base_error="invalid_auth"),
    test.case("invalid_station", side_effect=NoWeatherStationFound, base_error="invalid_station"),
    test.case("more_stations", side_effect=MultipleWeatherStationsFound, base_error="more_stations"),
    test.case("cannot_connect", side_effect=Exception, base_error="cannot_connect"),
)
async def flow_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    side_effect: type[Exception],
    base_error: str,
) -> None:
    """Test config flow errors."""
    result4 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result4["type"]).to_be(FlowResultType.FORM)
    expect(result4["step_id"]).to_equal(config_entries.SOURCE_USER)

    with patch(
        "homeassistant.components.trafikverket_weatherstation.config_flow.TrafikverketWeather.async_get_weather",
        side_effect=side_effect(),
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result4["flow_id"],
            user_input={
                CONF_API_KEY: "1234567890",
                CONF_STATION: "Vallby",
            },
        )

    expect(result4["errors"]).to_equal({"base": base_error})


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a reauthentication flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "1234567890",
            CONF_STATION: "Vallby",
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.trafikverket_weatherstation.config_flow.TrafikverketWeather.async_get_weather",
        ),
        patch(
            "homeassistant.components.trafikverket_weatherstation.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "1234567891"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal({"api_key": "1234567891", "station": "Vallby"})


@test.cases(
    test.case("invalid_auth", side_effect=InvalidAuthentication, base_error="invalid_auth"),
    test.case("invalid_station", side_effect=NoWeatherStationFound, base_error="invalid_station"),
    test.case("more_stations", side_effect=MultipleWeatherStationsFound, base_error="more_stations"),
    test.case("cannot_connect", side_effect=Exception, base_error="cannot_connect"),
)
async def reauth_flow_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    side_effect: type[Exception],
    base_error: str,
) -> None:
    """Test a reauthentication flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "1234567890",
            CONF_STATION: "Vallby",
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.trafikverket_weatherstation.config_flow.TrafikverketWeather.async_get_weather",
        side_effect=side_effect(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "1234567891"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": base_error})


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a reconfigure flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "1234567890",
            CONF_STATION: "Vallby",
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.trafikverket_weatherstation.config_flow.TrafikverketWeather.async_get_weather",
        ),
        patch(
            "homeassistant.components.trafikverket_weatherstation.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "1234567891", CONF_STATION: "Vallby_new"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal({"api_key": "1234567891", "station": "Vallby_new"})


@test.cases(
    test.case("invalid_auth", side_effect=InvalidAuthentication, base_error="invalid_auth"),
    test.case("invalid_station", side_effect=NoWeatherStationFound, base_error="invalid_station"),
    test.case("more_stations", side_effect=MultipleWeatherStationsFound, base_error="more_stations"),
    test.case("cannot_connect", side_effect=Exception, base_error="cannot_connect"),
)
async def reconfigure_flow_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    side_effect: type[Exception],
    base_error: str,
) -> None:
    """Test a reauthentication flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "1234567890",
            CONF_STATION: "Vallby",
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.trafikverket_weatherstation.config_flow.TrafikverketWeather.async_get_weather",
        side_effect=side_effect(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "1234567891", CONF_STATION: "Vallby_new"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": base_error})

    with (
        patch(
            "homeassistant.components.trafikverket_weatherstation.config_flow.TrafikverketWeather.async_get_weather",
        ),
        patch(
            "homeassistant.components.trafikverket_weatherstation.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "1234567891", CONF_STATION: "Vallby_new"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal({"api_key": "1234567891", "station": "Vallby_new"})
