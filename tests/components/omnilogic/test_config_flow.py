"""Test the Omnilogic config flow."""

from __future__ import annotations

from unittest.mock import patch

from omnilogic import LoginException, OmniLogicException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.omnilogic.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DATA = {"username": "test-username", "password": "test-password"}


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
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.omnilogic.config_flow.OmniLogic.connect",
            return_value=True,
        ),
        patch(
            "homeassistant.components.omnilogic.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            DATA,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Omnilogic")
    expect(result2["data"]).to_equal(DATA)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def already_configured(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test config flow when Omnilogic component is already setup."""
    MockConfigEntry(domain="omnilogic", data=DATA).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def with_invalid_credentials(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test with invalid credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.omnilogic.OmniLogic.connect",
        side_effect=LoginException,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            DATA,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test if invalid response or no connection returned from Hayward."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.omnilogic.OmniLogic.connect",
        side_effect=OmniLogicException,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            DATA,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def with_unknown_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test with unknown error response from Hayward."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.omnilogic.OmniLogic.connect",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            DATA,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "unknown"})


@test
async def option_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test option flow."""
    entry = MockConfigEntry(domain=DOMAIN, data=DATA)
    entry.add_to_hass(hass)

    expect(bool(entry.options)).to_equal(False)

    with patch(
        "homeassistant.components.omnilogic.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.options.async_init(
            entry.entry_id,
            data=None,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"polling_interval": 9},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("")
    expect(result["data"]["polling_interval"]).to_equal(9)
