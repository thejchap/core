"""Test the NextBus config flow."""

from __future__ import annotations

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries, setup
from homeassistant.components.nextbus.const import CONF_AGENCY, CONF_ROUTE, DOMAIN
from homeassistant.const import CONF_STOP
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.nextbus._fixtures import (
    DIRECTIONS_BOTH,
    DIRECTIONS_OUTBOUND_HIDDEN,
    make_mock_nextbus_lists,
    mock_nextbus,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _mse: MagicMock = Depends(mock_setup_entry),
) -> None:
    """Wire mocks for every test."""


@test.cases(
    test.case("outbound_hidden", DIRECTIONS_OUTBOUND_HIDDEN),
    test.case("both_directions", DIRECTIONS_BOTH),
)
async def user_config(
    directions: list[dict],
    hass: HomeAssistant = Depends(hass_fixture),
    mock_nextbus_: MagicMock = Depends(mock_nextbus),
    mock_setup: MagicMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    make_mock_nextbus_lists(mock_nextbus_, directions)
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("agency")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_AGENCY: "sfmta-cis"},
    )
    await hass.async_block_till_done()

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("route")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ROUTE: "F"},
    )
    await hass.async_block_till_done()

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("stop")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_STOP: "5184"},
    )
    await hass.async_block_till_done()

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("data")).to_equal(
        {
            "agency": "sfmta-cis",
            "route": "F",
            "stop": "5184",
        }
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)
