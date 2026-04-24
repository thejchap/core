"""Test the ProgettiHWSW Automation config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.progettihwsw.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

mock_value_step_user = {
    "title": "1R & 1IN Board",
    "relays": 1,
    "inputs": 1,
    "temps": False,
}


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
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_value_step_rm = {
        "relay_1": "bistable",
    }

    with patch(
        "homeassistant.components.progettihwsw.config_flow.ProgettiHWSWAPI.check_board",
        return_value=mock_value_step_user,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "", CONF_PORT: 80},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("relay_modes")
    expect(result2["errors"]).to_equal({})

    with patch(
        "homeassistant.components.progettihwsw.async_setup_entry",
        return_value=True,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            mock_value_step_rm,
        )

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(bool(result3["data"])).to_be(True)
    expect(result3["data"]["title"]).to_equal("1R & 1IN Board")
    expect(result3["data"]["is_old"]).to_be(False)
    expect(result3["data"]["relay_count"]).to_equal(1)
    expect(result3["data"]["input_count"]).to_equal(1)


@test
async def form_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle unexisting board."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.progettihwsw.config_flow.ProgettiHWSWAPI.check_board",
        return_value=False,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "", CONF_PORT: 80},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_existing_entry_exception(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle existing board."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["step_id"]).to_equal("user")

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "",
            CONF_PORT: 80,
        },
    )
    entry.add_to_hass(hass)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "", CONF_PORT: 80},
    )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def form_user_exception(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle unknown exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.progettihwsw.config_flow.validate_input",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "", CONF_PORT: 80},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "unknown"})
