"""Test OpenSky config flow."""

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

from . import setup_integration
from ._fixtures import config_entry, mock_setup_entry, opensky_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _setup: AsyncMock = Depends(mock_setup_entry),
    _network: None = Depends(mock_network),
) -> None:
    """Module-level fixture priming common mocks."""


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
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
        user_input={CONF_USERNAME: "homeassistant", CONF_CONTRIBUTING_USER: False},
        error="password_missing",
    ),
    test.case(
        "username_missing",
        user_input={CONF_PASSWORD: "secret", CONF_CONTRIBUTING_USER: False},
        error="username_missing",
    ),
    test.case(
        "no_authentication",
        user_input={CONF_CONTRIBUTING_USER: True},
        error="no_authentication",
    ),
    test.case(
        "invalid_auth",
        user_input={
            CONF_USERNAME: "homeassistant",
            CONF_PASSWORD: "secret",
            CONF_CONTRIBUTING_USER: True,
        },
        error="invalid_auth",
    ),
)
async def options_flow_failures(
    user_input: dict[str, Any],
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(opensky_client),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test load and unload entry."""
    await setup_integration(hass, entry)

    client.authenticate.side_effect = OpenSkyUnauthenticatedError
    result = await hass.config_entries.options.async_init(entry.entry_id)
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
    client.authenticate.side_effect = None
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(opensky_client),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test options flow."""
    await setup_integration(hass, entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
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
