"""Test the NextBus config flow."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries, setup
from homeassistant.components.nextbus.const import CONF_AGENCY, CONF_ROUTE, DOMAIN
from homeassistant.const import CONF_STOP
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_nextbus, mock_nextbus_lists, mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def user_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    _lists: MagicMock = Depends(mock_nextbus_lists),
) -> None:
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("agency")

    # Select agency
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_AGENCY: "sfmta-cis",
        },
    )
    await hass.async_block_till_done()

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("route")

    # Select route
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ROUTE: "F",
        },
    )
    await hass.async_block_till_done()

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("stop")

    # Select stop
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_STOP: "5184",
        },
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

    expect(len(setup_entry.mock_calls)).to_equal(1)
