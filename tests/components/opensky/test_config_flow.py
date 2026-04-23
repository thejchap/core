"""Test OpenSky config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

from python_opensky.exceptions import OpenSkyUnauthenticatedError
from tryke import Depends, expect, fixture, test

from homeassistant.components.opensky.const import (
    CONF_ALTITUDE,
    CONF_CONTRIBUTING_USER,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_PASSWORD,
    CONF_RADIUS,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from . import setup_integration
from ._fixtures import (
    config_entry as config_entry_fx,
    mock_setup_entry as mock_setup_entry_fx,
    opensky_client as opensky_client_fx,
)


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def full_user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_RADIUS: 10,
            CONF_LATITUDE: 0.0,
            CONF_LONGITUDE: 0.0,
            CONF_ALTITUDE: 0,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OpenSky")
    expect(result["data"]).to_equal(
        {
            CONF_LATITUDE: 0.0,
            CONF_LONGITUDE: 0.0,
        }
    )
    expect(result["options"]).to_equal(
        {
            CONF_ALTITUDE: 0.0,
            CONF_RADIUS: 10.0,
        }
    )


@test.cases(
    test.case(
        "password_missing",
        {CONF_USERNAME: "homeassistant", CONF_CONTRIBUTING_USER: False},
        "password_missing",
    ),
    test.case(
        "username_missing",
        {CONF_PASSWORD: "secret", CONF_CONTRIBUTING_USER: False},
        "username_missing",
    ),
    test.case(
        "no_authentication",
        {CONF_CONTRIBUTING_USER: True},
        "no_authentication",
    ),
    test.case(
        "invalid_auth",
        {
            CONF_USERNAME: "homeassistant",
            CONF_PASSWORD: "secret",
            CONF_CONTRIBUTING_USER: True,
        },
        "invalid_auth",
    ),
)
async def options_flow_failures(
    user_input: dict[str, Any],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    opensky_client: AsyncMock = Depends(opensky_client_fx),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
) -> None:
    """Test load and unload entry."""
    await setup_integration(hass, config_entry)

    opensky_client.authenticate.side_effect = OpenSkyUnauthenticatedError
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_RADIUS: 10000, **user_input},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    expect(result["errors"]["base"]).to_equal(error)
    opensky_client.authenticate.side_effect = None
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_RADIUS: 10000,
            CONF_USERNAME: "homeassistant",
            CONF_PASSWORD: "secret",
            CONF_CONTRIBUTING_USER: True,
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_RADIUS: 10000,
            CONF_USERNAME: "homeassistant",
            CONF_PASSWORD: "secret",
            CONF_CONTRIBUTING_USER: True,
        }
    )


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    opensky_client: AsyncMock = Depends(opensky_client_fx),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
) -> None:
    """Test options flow."""
    await setup_integration(hass, config_entry)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_RADIUS: 10000,
            CONF_USERNAME: "homeassistant",
            CONF_PASSWORD: "secret",
            CONF_CONTRIBUTING_USER: True,
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_RADIUS: 10000,
            CONF_USERNAME: "homeassistant",
            CONF_PASSWORD: "secret",
            CONF_CONTRIBUTING_USER: True,
        }
    )
