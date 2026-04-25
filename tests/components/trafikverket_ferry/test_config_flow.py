"""Test the Trafikverket Ferry config flow."""

from __future__ import annotations

from unittest.mock import patch

from pytrafikverket.exceptions import InvalidAuthentication, NoFerryFound
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.trafikverket_ferry.const import (
    CONF_FROM,
    CONF_TIME,
    CONF_TO,
    DOMAIN,
)
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_WEEKDAY, WEEKDAYS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


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
            "homeassistant.components.trafikverket_ferry.config_flow.TrafikverketFerry.async_get_next_ferry_stop",
        ),
        patch(
            "homeassistant.components.trafikverket_ferry.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "1234567890",
                CONF_FROM: "Ekerö",
                CONF_TO: "Slagsta",
                CONF_TIME: "10:00",
                CONF_WEEKDAY: ["mon", "fri"],
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Ekerö to Slagsta at 10:00")
    expect(result2["data"]).to_equal(
        {
            "api_key": "1234567890",
            "name": "Ekerö to Slagsta at 10:00",
            "from": "Ekerö",
            "to": "Slagsta",
            "time": "10:00",
            "weekday": ["mon", "fri"],
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(result2["result"].unique_id).to_equal("ekerö-slagsta-10:00-['mon', 'fri']")


@test.cases(
    test.case(
        "invalid_auth", side_effect=InvalidAuthentication, base_error="invalid_auth"
    ),
    test.case("invalid_route", side_effect=NoFerryFound, base_error="invalid_route"),
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
        "homeassistant.components.trafikverket_ferry.config_flow.TrafikverketFerry.async_get_next_ferry_stop",
        side_effect=side_effect(),
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result4["flow_id"],
            user_input={
                CONF_API_KEY: "1234567890",
                CONF_FROM: "Ekerö",
                CONF_TO: "Slagsta",
                CONF_TIME: "00:00",
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
            CONF_NAME: "Ekerö to Slagsta at 10:00",
            CONF_FROM: "Ekerö",
            CONF_TO: "Slagsta",
            CONF_TIME: "10:00",
            CONF_WEEKDAY: WEEKDAYS,
        },
        unique_id=f"ekerö-slagsta-10:00-{WEEKDAYS}",
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.trafikverket_ferry.config_flow.TrafikverketFerry.async_get_next_ferry_stop",
        ),
        patch(
            "homeassistant.components.trafikverket_ferry.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "1234567891"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal(
        {
            "api_key": "1234567891",
            "name": "Ekerö to Slagsta at 10:00",
            "from": "Ekerö",
            "to": "Slagsta",
            "time": "10:00",
            "weekday": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        }
    )


@test.cases(
    test.case(
        "invalid_auth", side_effect=InvalidAuthentication, p_error="invalid_auth"
    ),
    test.case("invalid_route", side_effect=NoFerryFound, p_error="invalid_route"),
    test.case("cannot_connect", side_effect=Exception, p_error="cannot_connect"),
)
async def reauth_flow_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    side_effect: type[Exception],
    p_error: str,
) -> None:
    """Test a reauthentication flow with error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "1234567890",
            CONF_NAME: "Ekerö to Slagsta at 10:00",
            CONF_FROM: "Ekerö",
            CONF_TO: "Slagsta",
            CONF_TIME: "10:00",
            CONF_WEEKDAY: WEEKDAYS,
        },
        unique_id=f"ekerö-slagsta-10:00-{WEEKDAYS}",
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    with patch(
        "homeassistant.components.trafikverket_ferry.config_flow.TrafikverketFerry.async_get_next_ferry_stop",
        side_effect=side_effect(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "1234567890"},
        )
        await hass.async_block_till_done()

    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": p_error})

    with (
        patch(
            "homeassistant.components.trafikverket_ferry.config_flow.TrafikverketFerry.async_get_next_ferry_stop",
        ),
        patch(
            "homeassistant.components.trafikverket_ferry.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "1234567891"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal(
        {
            "api_key": "1234567891",
            "name": "Ekerö to Slagsta at 10:00",
            "from": "Ekerö",
            "to": "Slagsta",
            "time": "10:00",
            "weekday": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        }
    )
