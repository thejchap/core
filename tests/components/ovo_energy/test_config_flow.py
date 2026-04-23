"""Test the OVO Energy config flow."""

from __future__ import annotations

from unittest.mock import patch

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.ovo_energy.const import CONF_ACCOUNT, DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

FIXTURE_REAUTH_INPUT = {CONF_PASSWORD: "something1"}
FIXTURE_USER_INPUT = {
    CONF_USERNAME: "example@example.com",
    CONF_PASSWORD: "something",
    CONF_ACCOUNT: "123456",
}

UNIQUE_ID = "example@example.com"


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def show_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the setup form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def authorization_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we show user form on connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.ovo_energy.config_flow.OVOEnergy.authenticate",
            return_value=False,
        ),
        patch(
            "homeassistant.components.ovo_energy.config_flow.OVOEnergy.bootstrap_accounts",
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def connection_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we show user form on connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.ovo_energy.config_flow.OVOEnergy.authenticate",
        side_effect=aiohttp.ClientError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def full_flow_implementation(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test registering an integration and finishing flow works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.ovo_energy.config_flow.OVOEnergy.authenticate",
            return_value=True,
        ),
        patch(
            "homeassistant.components.ovo_energy.config_flow.OVOEnergy.bootstrap_accounts",
        ),
        patch(
            "homeassistant.components.ovo_energy.config_flow.OVOEnergy.username",
            "some_name",
        ),
        patch(
            "homeassistant.components.ovo_energy.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"][CONF_USERNAME]).to_equal(FIXTURE_USER_INPUT[CONF_USERNAME])
    expect(result2["data"][CONF_PASSWORD]).to_equal(FIXTURE_USER_INPUT[CONF_PASSWORD])
    expect(result2["data"][CONF_ACCOUNT]).to_equal(FIXTURE_USER_INPUT[CONF_ACCOUNT])


@test
async def reauth_authorization_error(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we show user form on authorization error."""
    mock_config = MockConfigEntry(
        domain=DOMAIN, unique_id=UNIQUE_ID, data=FIXTURE_USER_INPUT
    )
    mock_config.add_to_hass(hass)
    result = await mock_config.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    with patch(
        "homeassistant.components.ovo_energy.config_flow.OVOEnergy.authenticate",
        return_value=False,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_REAUTH_INPUT,
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("reauth_confirm")
        expect(result2["errors"]).to_equal({"base": "authorization_error"})


@test
async def reauth_connection_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we show user form on connection error."""
    mock_config = MockConfigEntry(
        domain=DOMAIN, unique_id=UNIQUE_ID, data=FIXTURE_USER_INPUT
    )
    mock_config.add_to_hass(hass)
    result = await mock_config.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.ovo_energy.config_flow.OVOEnergy.authenticate",
        side_effect=aiohttp.ClientError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_REAUTH_INPUT,
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("reauth_confirm")
        expect(result2["errors"]).to_equal({"base": "connection_error"})


@test
async def reauth_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test reauth works."""
    mock_config = MockConfigEntry(
        domain=DOMAIN, unique_id=UNIQUE_ID, data=FIXTURE_USER_INPUT
    )
    mock_config.add_to_hass(hass)
    result = await mock_config.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.ovo_energy.config_flow.OVOEnergy.authenticate",
        return_value=False,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_REAUTH_INPUT,
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("reauth_confirm")
        expect(result["errors"]).to_equal({"base": "authorization_error"})

    with (
        patch(
            "homeassistant.components.ovo_energy.config_flow.OVOEnergy.authenticate",
            return_value=True,
        ),
        patch(
            "homeassistant.components.ovo_energy.config_flow.OVOEnergy.username",
            return_value=FIXTURE_USER_INPUT[CONF_USERNAME],
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_REAUTH_INPUT,
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("reauth_successful")
