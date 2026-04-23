"""Test the P1 Monitor config flow."""

from __future__ import annotations

from unittest.mock import patch

from p1monitor import P1MonitorError
from tryke import Depends, expect, fixture, test

from homeassistant.components.p1_monitor.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def full_user_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    with (
        patch(
            "homeassistant.components.p1_monitor.config_flow.P1Monitor.settings"
        ) as mock_p1monitor,
        patch(
            "homeassistant.components.p1_monitor.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "example.com", CONF_PORT: 80},
        )

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("P1 Monitor")
    expect(result2.get("data")).to_equal({CONF_HOST: "example.com", CONF_PORT: 80})
    expect(isinstance(result2["data"][CONF_PORT], int)).to_be(True)

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_p1monitor.mock_calls)).to_equal(1)


@test
async def api_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle cannot connect error."""
    with patch(
        "homeassistant.components.p1_monitor.coordinator.P1Monitor.settings",
        side_effect=P1MonitorError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_HOST: "example.com", CONF_PORT: 80},
        )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": "cannot_connect"})
