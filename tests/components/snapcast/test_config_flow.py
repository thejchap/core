"""Test the Snapcast module."""

from __future__ import annotations

import socket
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.snapcast.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_server, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_CONNECTION = {CONF_HOST: "127.0.0.1", CONF_PORT: 1705}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    server: AsyncMock = Depends(mock_server),
) -> None:
    """Test the full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_CONNECTION,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Snapcast")
    expect(result["data"]).to_equal({CONF_HOST: "127.0.0.1", CONF_PORT: 1705})
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("gaierror", exception=socket.gaierror, error="invalid_host"),
    test.case(
        "conn_refused", exception=ConnectionRefusedError, error="cannot_connect"
    ),
)
async def exceptions(
    exception: type[Exception],
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    server: AsyncMock = Depends(mock_server),
) -> None:
    """Test we get the form and handle errors and successful connection."""
    server.side_effect = exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_CONNECTION,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error})

    server.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_CONNECTION,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test config flow abort if device is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_CONNECTION,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
